"""測試模式：假資料、/_test/* API、推播紀錄、CLI。"""

import pytest

from app.cli import main as cli
from app.config import get_settings
from app.features.devices import repository as devices_repo
from app.tools import db

P = "/assistive/v1"
TOKEN = "phone-token-1234567890"


@pytest.fixture
def test_mode(monkeypatch):
    monkeypatch.setattr(get_settings(), "test_mode", True)
    db.execute("DELETE FROM push_log")


def test_test_api_hidden_when_not_test_mode(client):
    assert client.get(f"{P}/_test/state").status_code == 404


def test_fake_data_is_large_and_varied(client, test_mode):
    cats = client.get(f"{P}/catalog").json()["categories"]
    variants = [v for c in cats for v in c["variants"]]
    assert len(cats) == 12 and len(variants) == 62
    assert any(v["image"] is None for v in variants) and any(v["specs"] == [] for v in variants)
    assert any(v["attrs"] is None for v in variants) and any(v["description"] is None for v in variants)
    assert len(client.get(f"{P}/centers").json()["centers"]) == 3
    days = client.get(f"{P}/centers/south/calendar?from=2026-11-01&days=30").json()["days"]
    assert len(days) == 30 and {d["reason"] for d in days} >= {"例假日休館", "測試國定假日", "臨時休館"}


def test_full_flow_with_push_log(client, test_mode):
    r = client.post(f"{P}/_test/scenario", json={"token": TOKEN}).json()
    rid, mb = r["reservation"]["id"], r["mailbox_id"]
    assert r["reservation"]["status"] == "booked" and devices_repo.get(TOKEN).mailbox_id == mb

    assert client.post(f"{P}/_test/reservations/{rid}/trigger", json={"event": "pickup_reminder"}).status_code == 200
    out = client.post(f"{P}/_test/reservations/{rid}/trigger", json={"event": "expired"}).json()
    assert out["status"] == "expired"
    # 逾期的不能再逾期
    assert client.post(f"{P}/_test/reservations/{rid}/trigger", json={"event": "expired"}).status_code == 409

    state = client.get(f"{P}/_test/state").json()
    pushes = [p for p in reversed(state["recent_pushes"]) if p["mailbox_id"] == mb]
    assert [p["type"] for p in pushes] == ["reservation.booked", "reservation.pickup_reminder",
                                           "reservation.expired"]
    assert all(p["result"] == "local" for p in pushes)  # 沒設定 FCM：只記錄在本機
    assert pushes[0]["data"]["reservation_id"] == rid

    # 信箱裡也有同樣的事件（pull 補拉）
    events = client.get(f"{P}/mailboxes/{mb}/events?wait=0",
                        headers={"Authorization": f"Bearer {r['mailbox_key']}"}).json()["events"]
    assert [e["type"] for e in events] == [p["type"] for p in pushes]


def test_flow_without_token_uses_local_device(client, test_mode):
    r = client.post(f"{P}/_test/scenario", json={}).json()
    assert r["device_token"] == f"local-{r['mailbox_id']}"
    client.post(f"{P}/_test/reservations/{r['reservation']['id']}/trigger", json={"event": "expired"})
    pushes = [p for p in client.get(f"{P}/_test/state").json()["recent_pushes"] if p["mailbox_id"] == r["mailbox_id"]]
    assert [p["type"] for p in reversed(pushes)] == ["reservation.booked", "reservation.expired"]
    assert {p["result"] for p in pushes} == {"local"}


def test_stock_and_notice_triggers(client, test_mode):
    r = client.post(f"{P}/_test/scenario", json={"token": TOKEN}).json()
    auth = {"Authorization": f"Bearer {r['mailbox_key']}"}
    client.post(f"{P}/_test/stock", json={"variant_id": "181", "stock": 0, "waiting": 3})
    assert client.post(f"{P}/subscriptions", json={"mailbox_id": r["mailbox_id"], "variant_id": "181"},
                       headers=auth).status_code == 201
    assert client.post(f"{P}/_test/stock", json={"variant_id": "181", "stock": 2}).json()["changed"]
    assert client.post(f"{P}/_test/notices", json={"title": "測試公告"}).json()["mailboxes"] == 1

    pushes = client.get(f"{P}/_test/state").json()["recent_pushes"]
    types = [p["type"] for p in reversed(pushes)]
    assert "stock.arrived" in types and types[-1] == "service.notice"
    assert pushes[0]["target"] == "topic:assistive-notice"


def test_cli_direct_push_and_outbox(test_mode, capsys):
    devices_repo.reset()
    from app.features.devices import service

    service.register("mb_cli", "fcm", TOKEN)
    cli(["devices"])
    cli(["push", "--mailbox", "mb_cli", "--type", "stock.arrived"])
    cli(["topic", "--title", "CLI 公告"])
    cli(["outbox", "-n", "5"])
    out = capsys.readouterr().out
    assert TOKEN in out
    assert "到貨通知｜你訂閱的輔具已到貨，可以預約了" in out
    assert "topic:assistive-notice" in out and "CLI 公告" in out


def test_api_switches_in_config(monkeypatch):
    from fastapi.testclient import TestClient

    from app import config
    from app.main import create_app

    monkeypatch.setitem(config.API_ENABLED, "reservations", False)
    monkeypatch.setitem(config.API_ENABLED, "devices", False)
    c = TestClient(create_app())
    assert c.post(f"{P}/reservations", json={}).status_code == 404
    assert c.post(f"{P}/devices", json={}).status_code == 404
    assert c.get(f"{P}/health").status_code == 200


def test_test_api_needs_config_and_env(client, monkeypatch):
    from fastapi.testclient import TestClient

    from app import config
    from app.main import create_app

    monkeypatch.setattr(get_settings(), "test_mode", True)
    assert client.get(f"{P}/_test/panel").status_code == 200
    monkeypatch.setitem(config.API_ENABLED, "test", False)
    assert TestClient(create_app()).get(f"{P}/_test/state").status_code == 404


def test_panel_endpoints_direct_push_and_events(client, test_mode):
    html = client.get(f"{P}/_test/panel")
    assert html.status_code == 200 and "推播測試面板" in html.text

    d = client.post(f"{P}/_test/devices", json={}).json()
    mb = d["mailbox_id"]
    assert d["device_token"] == f"local-{mb}" and d["mailbox_key"]
    d2 = client.post(f"{P}/_test/devices", json={"token": TOKEN, "mailbox_id": mb}).json()
    assert d2["mailbox_key"] is None and devices_repo.get(TOKEN).mailbox_id == mb

    for t in ("reservation.booked", "stock.arrived", "service.notice"):
        res = client.post(f"{P}/_test/push", json={"type": t, "mailbox_id": mb, "title": "面板公告"}).json()
        assert len(res["results"]) == 2 and {r["result"] for r in res["results"]} == {"local"}
    topic = client.post(f"{P}/_test/push", json={"type": "service.notice", "topic": True, "title": "T"}).json()
    assert topic["results"][0]["target"] == "topic:assistive-notice"
    assert client.post(f"{P}/_test/push", json={"type": "stock.arrived"}).status_code == 422

    client.post(f"{P}/_test/notices", json={"title": "寫入信箱"})
    ev = client.get(f"{P}/_test/events?mailbox_id={mb}").json()["events"]
    assert [e["type"] for e in ev] == ["service.notice"]
    assert client.get(f"{P}/_test/events?mailbox_id=nope").status_code == 404


def test_simulated_changes_trigger_pushes(client, test_mode):
    r = client.post(f"{P}/_test/scenario", json={}).json()
    auth = {"Authorization": f"Bearer {r['mailbox_key']}"}
    zero = [v for v, x in client.get(f"{P}/stock").json()["items"].items() if x["stock"] == 0]
    assert client.post(f"{P}/subscriptions", json={"mailbox_id": r["mailbox_id"], "variant_id": zero[0]},
                       headers=auth).status_code == 201

    first = client.post(f"{P}/_test/sync").json()
    assert first["stock_changed"] > 0
    assert any(p["type"] == "stock.arrived" for p in first["pushes"])
    assert client.get(f"{P}/stock").json()["items"][zero[0]]["stock"] > 0

    types = [p["type"] for _ in range(3) for p in client.post(f"{P}/_test/sync").json()["pushes"]]
    assert "service.notice" in types  # 每 3 次出現一則新公告
