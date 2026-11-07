"""到貨通知：每次抓資料後，等待中且有貨的訂閱 → SQL 狀態 arrived → 只推給訂閱人的裝置。"""

import sqlite3

import pytest

from app.config import get_settings
from app.features.devices import service as devices_service
from app.tools import db
from tests.test_api import P

TOKEN_ME = "token-me-0000000000"
TOKEN_OTHER = "token-other-000000000"


@pytest.fixture
def test_mode(monkeypatch):
    monkeypatch.setattr(get_settings(), "test_mode", True)
    db.execute("DELETE FROM push_log")


def mailbox(client, token):
    mb = client.post(f"{P}/mailboxes").json()
    devices_service.register(mb["mailbox_id"], "fcm", token)
    return mb["mailbox_id"], {"Authorization": f"Bearer {mb['mailbox_key']}"}


def zero_stock(client):
    items = client.get(f"{P}/stock").json()["items"]
    return [v for v, x in items.items() if x["stock"] == 0]


def category(client):
    return {v["id"]: c["id"] for c in client.get(f"{P}/catalog").json()["categories"] for v in c["variants"]}


def test_all_waiting_subscriptions_arrive_and_push_only_to_owner(client, test_mode):
    client.post(f"{P}/_test/sync")
    me, my_auth = mailbox(client, TOKEN_ME)
    other, _ = mailbox(client, TOKEN_OTHER)  # 沒訂閱的人不該收到

    cat, picked, seen = category(client), [], set()
    for v in zero_stock(client):  # 每類挑一個（同類只能訂一個）
        if cat[v] not in seen:
            seen.add(cat[v])
            picked.append(v)
        if len(picked) == 3:
            break
    for v in picked:
        assert client.post(f"{P}/subscriptions", json={"mailbox_id": me, "variant_id": v},
                           headers=my_auth).status_code == 201
    subs = client.get(f"{P}/subscriptions?mailbox_id={me}", headers=my_auth).json()
    assert [s["status"] for s in subs] == ["waiting"] * 3

    r = client.post(f"{P}/_test/sync").json()

    subs = client.get(f"{P}/subscriptions?mailbox_id={me}", headers=my_auth).json()
    assert [s["status"] for s in subs] == ["arrived"] * 3 and all(s["arrived_at"] for s in subs)
    rows = db.query("SELECT status FROM subscriptions WHERE mailbox_id = ?", (me,))
    assert [x["status"] for x in rows] == ["arrived"] * 3  # SQL 裡也是 arrived

    arrived = [p for p in r["pushes"] if p["type"] == "stock.arrived"]
    assert len(arrived) == 3
    log = db.query("SELECT target, mailbox_id FROM push_log WHERE type = 'stock.arrived'")
    assert {x["mailbox_id"] for x in log} == {me}  # 只推給訂閱人
    assert all(x["target"].startswith(TOKEN_ME[:12]) for x in log)  # 推到他的裝置，不是 topic

    # 已到貨的不會重複推
    again = client.post(f"{P}/_test/sync").json()
    assert not [p for p in again["pushes"] if p["type"] == "stock.arrived"]


def test_subscribe_in_stock_item_arrives_on_next_sync(client, test_mode):
    client.post(f"{P}/_test/sync")
    me, auth = mailbox(client, TOKEN_ME)
    items = client.get(f"{P}/stock").json()["items"]
    in_stock = next(v for v, x in items.items() if x["stock"] > 0)
    client.post(f"{P}/subscriptions", json={"mailbox_id": me, "variant_id": in_stock}, headers=auth)
    client.post(f"{P}/_test/sync")
    assert client.get(f"{P}/subscriptions?mailbox_id={me}", headers=auth).json()[0]["status"] == "arrived"


def test_only_stock_count_people_notified_in_order(client, test_mode):
    client.post(f"{P}/_test/stock", json={"variant_id": "181", "stock": 0, "waiting": 2})
    first, a1 = mailbox(client, TOKEN_ME)
    second, a2 = mailbox(client, TOKEN_OTHER)
    for mb, auth in ((first, a1), (second, a2)):
        client.post(f"{P}/subscriptions", json={"mailbox_id": mb, "variant_id": "181"}, headers=auth)
    client.post(f"{P}/_test/stock", json={"variant_id": "181", "stock": 1, "waiting": 1})
    assert client.get(f"{P}/subscriptions?mailbox_id={first}", headers=a1).json()[0]["status"] == "arrived"
    assert client.get(f"{P}/subscriptions?mailbox_id={second}", headers=a2).json()[0]["status"] == "waiting"


def test_arrived_subscription_does_not_block_resubscribe(client, test_mode):
    client.post(f"{P}/_test/stock", json={"variant_id": "181", "stock": 0})
    me, auth = mailbox(client, TOKEN_ME)
    client.post(f"{P}/subscriptions", json={"mailbox_id": me, "variant_id": "181"}, headers=auth)
    client.post(f"{P}/_test/stock", json={"variant_id": "181", "stock": 2})
    client.post(f"{P}/_test/stock", json={"variant_id": "181", "stock": 0})
    res = client.post(f"{P}/subscriptions", json={"mailbox_id": me, "variant_id": "181"}, headers=auth)
    assert res.status_code == 201


def test_list_requires_key(client):
    mb = client.post(f"{P}/mailboxes").json()
    assert client.get(f"{P}/subscriptions?mailbox_id={mb['mailbox_id']}").json()["code"] == "BAD_KEY"


def test_old_db_file_gets_new_columns(tmp_path, monkeypatch):
    path = tmp_path / "old.db"
    old = sqlite3.connect(path)
    old.execute("CREATE TABLE subscriptions (seq INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT NOT NULL UNIQUE, "
                "mailbox_id TEXT NOT NULL, variant_id TEXT NOT NULL, category_id TEXT, created_at TEXT NOT NULL)")
    old.execute("INSERT INTO subscriptions(id, mailbox_id, variant_id, created_at) VALUES ('s1','m','181','x')")
    old.commit()
    old.close()
    monkeypatch.setattr(get_settings(), "db_path", str(path))
    db.close()
    try:
        row = db.query("SELECT status, arrived_at FROM subscriptions")[0]
        assert row["status"] == "waiting" and row["arrived_at"] is None
    finally:
        db.close()
        monkeypatch.undo()
        db.close()


def test_waiting_subscription_on_item_already_reset_to_zero_still_arrives(client, test_mode):
    """重啟後模擬狀態不見、DB 庫存跟假資料不一致時，等待中的訂閱也要到貨。"""
    from app.tools import testdata

    client.post(f"{P}/_test/sync")
    client.post(f"{P}/_test/stock", json={"variant_id": "181", "stock": 5})  # DB 有貨，假資料原本是 0
    me, auth = mailbox(client, TOKEN_ME)
    db.execute("INSERT INTO subscriptions(id, mailbox_id, variant_id, created_at) VALUES ('s-old', ?, '181', '2026-11-07T10:00:00+08:00')",
               (me,))
    testdata.reset_simulation()  # 模擬重啟
    client.post(f"{P}/_test/sync")
    assert db.query("SELECT status FROM subscriptions WHERE id = 's-old'")[0]["status"] == "arrived"
    assert client.get(f"{P}/stock").json()["items"]["181"]["stock"] > 0
