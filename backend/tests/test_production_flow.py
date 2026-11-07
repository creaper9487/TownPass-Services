"""正式模式（TEST_MODE=false）端到端：用真的爬蟲程式解析「官網 HTML」，只把網路換成固定網頁。

流程：目錄 / 庫存（官方代碼）→ 訂閱缺貨品項 → 官網到貨 → python -m app.cli sync
     → SQL 狀態 arrived → 只推給訂閱人；官網掛掉時目錄回上次的資料；測試 API 不開放。
"""

from datetime import date

import httpx
import pytest

from app.cli import main as cli
from app.config import get_settings
from app.features.devices import service as devices_service
from app.features.reservation import service as reservation_service
from app.tools import db
from app.tools.crawlers import _borrow_source as borrow
from app.tools.crawlers import _calendar_source as cal
from tests.test_api import CONTACT, P
from tests.test_crawlers import variant_html

OFFICIAL = {"185": ("0", "13"), "192": ("3", None)}  # 款式代碼 → (剩餘, 等待人數)


@pytest.fixture
def official_site(monkeypatch):
    """假的官網：/additem 兩個分類，各分類頁一款；site['down'] = True 模擬官網掛掉。"""
    site = {"down": False}
    client_class = httpx.Client

    def respond(request):
        if site["down"]:
            raise httpx.ConnectError("官網掛了", request=request)
        path = request.url.path
        if path.endswith("/additem"):
            cards = "".join(
                f'''<div class="ind-tab"><img src="/app37/tools/showvehiclemodel/{cid}" alt="{name}圖片">
                <button onclick="window.location.assign('/app37/rentView/vehicleDetail/{cid}')">查看</button></div>'''
                for cid, name in [("1", "輪椅"), ("20", "其他")])
            return httpx.Response(200, text='<div class="col-md-9">' + cards + "</div>")
        for cid, vid in (("1", "185"), ("20", "192")):
            if path.endswith(f"/vehicleDetail/{cid}"):
                stock, waiting = OFFICIAL[vid]
                return httpx.Response(200, text=variant_html(vid, stock, waiting, available=stock != "0"))
        raise httpx.ConnectError("公告頁離線", request=request)  # 休館公告 → 走回退

    def fresh():  # 每次 sync 都重新抓（爬蟲本身有 30 秒快照）
        monkeypatch.setattr(borrow, "_snapshot", None)
        monkeypatch.setattr(borrow, "_snapshot_at", 0)

    fake_client = lambda **kw: client_class(transport=httpx.MockTransport(respond), **kw)  # noqa: E731
    monkeypatch.setattr(borrow, "REQUEST_INTERVAL_SECONDS", 0)
    monkeypatch.setattr(borrow.httpx, "Client", fake_client)
    monkeypatch.setattr(cal, "_closures", None)
    monkeypatch.setattr(cal, "_closures_at", 0)
    monkeypatch.setattr(cal, "_notice_closures", {})
    monkeypatch.setattr(reservation_service, "today", lambda: date(2026, 11, 10))  # 週二，合宜有開
    site["fresh"] = fresh
    fresh()
    yield site
    OFFICIAL.update({"185": ("0", "13"), "192": ("3", None)})


def test_production_end_to_end(client, official_site, capsys):
    assert get_settings().test_mode is False
    assert client.get(f"{P}/_test/state").status_code == 404  # 正式模式不開測試 API

    cats = client.get(f"{P}/catalog").json()["categories"]
    assert [c["id"] for c in cats] == ["1", "20"]
    assert [v["id"] for c in cats for v in c["variants"]] == ["185", "192"]  # 官網代碼

    cli(["sync"])  # 抓一次庫存（= 背景每 3 分鐘做的事）
    assert "正式模式（官網資料）" in capsys.readouterr().out
    stock = client.get(f"{P}/stock").json()["items"]
    assert stock == {"185": {"stock": 0, "waiting": 13}, "192": {"stock": 3, "waiting": 0}}

    # 使用者：建信箱、登記手機、訂閱缺貨的 185、借有貨的 192
    mb = client.post(f"{P}/mailboxes").json()
    auth = {"Authorization": f"Bearer {mb['mailbox_key']}"}
    devices_service.register(mb["mailbox_id"], "fcm", "local-user-phone")
    other = client.post(f"{P}/mailboxes").json()
    devices_service.register(other["mailbox_id"], "fcm", "local-other-phone")
    assert client.post(f"{P}/subscriptions", json={"mailbox_id": mb["mailbox_id"], "variant_id": "NOPE"},
                       headers=auth).status_code == 422
    assert client.post(f"{P}/subscriptions", json={"mailbox_id": mb["mailbox_id"], "variant_id": "185"},
                       headers=auth).status_code == 201
    r = client.post(f"{P}/reservations", headers={"Idempotency-Key": "prod-1"}, json={
        "service": "borrow", "mailbox_id": mb["mailbox_id"], "center_id": "heyi", "items": ["192"],
        "contact": CONTACT})
    assert r.status_code == 201, r.text
    assert r.json()["pickup"] == {"deadline": "2026-11-11", "open_dates": ["2026-11-10", "2026-11-11"]}
    assert client.get(f"{P}/stock").json()["items"]["192"]["stock"] == 2  # 借用扣庫存

    # 官網沒變 → sync 不會推到貨
    official_site["fresh"]()
    cli(["sync"])
    subs = client.get(f"{P}/subscriptions?mailbox_id={mb['mailbox_id']}", headers=auth).json()
    assert subs[0]["status"] == "waiting"

    # 官網 185 到貨了 → sync → arrived → 只推給訂閱人
    OFFICIAL["185"] = ("1", "12")
    official_site["fresh"]()
    cli(["sync"])
    out = capsys.readouterr().out
    assert f"stock.arrived  信箱 {mb['mailbox_id']}  → 推播給 1 台裝置" in out
    subs = client.get(f"{P}/subscriptions?mailbox_id={mb['mailbox_id']}", headers=auth).json()
    assert subs[0]["status"] == "arrived" and subs[0]["arrived_at"]
    log = db.query("SELECT mailbox_id, target, title FROM push_log WHERE type = 'stock.arrived'")
    assert [(x["mailbox_id"], x["title"]) for x in log] == [(mb["mailbox_id"], "到貨通知")]
    assert not db.query("SELECT 1 FROM events WHERE type = 'service.notice'")  # 沒有任何假公告

    # 官網掛掉：目錄回上次的資料、sync 回報錯誤不會當掉
    from app.features.catalog import service as catalog_service

    catalog_service._cache.clear()
    official_site["down"] = True
    official_site["fresh"]()
    assert [c["id"] for c in client.get(f"{P}/catalog").json()["categories"]] == ["1", "20"]
    cli(["sync"])
    assert "stock: SOURCE_UNAVAILABLE" in capsys.readouterr().out
    assert client.get(f"{P}/stock").json()["items"]["185"]["stock"] == 1  # 庫存維持最後一次的值


def test_catalog_503_when_never_fetched(client, official_site):
    official_site["down"] = True
    res = client.get(f"{P}/catalog")
    assert res.status_code == 503 and res.json()["code"] == "SOURCE_UNAVAILABLE"


def test_cli_state_works_in_production(capsys):
    cli(["state"])
    out = capsys.readouterr().out
    assert "到貨訂閱" in out and "裝置" in out


def test_cli_arrive_forces_all_waiting_and_pushes_each_owner(client, official_site, capsys):
    cli(["sync"])  # 185 缺貨、192 有貨
    people = []
    for token in ("local-phone-a", "local-phone-b"):
        mb = client.post(f"{P}/mailboxes").json()
        devices_service.register(mb["mailbox_id"], "fcm", token)
        auth = {"Authorization": f"Bearer {mb['mailbox_key']}"}
        assert client.post(f"{P}/subscriptions", json={"mailbox_id": mb["mailbox_id"], "variant_id": "185"},
                           headers=auth).status_code == 201
        people.append((mb["mailbox_id"], auth))

    cli(["arrive"])  # 官網沒到貨也直接全部改
    out = capsys.readouterr().out
    assert "✓ 2 筆訂閱改成已到貨" in out
    for mailbox_id, auth in people:
        subs = client.get(f"{P}/subscriptions?mailbox_id={mailbox_id}", headers=auth).json()
        assert subs[0]["status"] == "arrived"
    log = db.query("SELECT mailbox_id FROM push_log WHERE type = 'stock.arrived'")
    assert sorted(x["mailbox_id"] for x in log) == sorted(m for m, _ in people)  # 各推給各自的人

    cli(["arrive"])  # 再跑一次：沒有等待中的了，不重複推
    assert "沒有等待中的到貨訂閱" in capsys.readouterr().out
