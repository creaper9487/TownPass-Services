"""主動推播：裝置登記、事件 → FCM、文案不含敏感資訊、失效 token、重試、公告檢查。"""

import asyncio
from datetime import datetime, timedelta

import pytest

from app import config
from app.features.centers import service as centers_service
from app.features.devices import repository as devices_repo
from app.features.notification import notice_watch
from app.features.notification import service as notification_service
from app.tools import fcm
from app.tools.crawlers.schemas import CalendarDay
from app.tools.timeutil import TAIPEI, today

from tests.test_api import CONTACT, P, borrow_body, new_mailbox, signed_post

TOKEN_A = "token-aaaaaaaaaaaa"
TOKEN_B = "token-bbbbbbbbbbbb"


@pytest.fixture
def fake_fcm(monkeypatch):
    """攔截 FCM：記錄送出的訊息，可指定每個 token 的回應。"""
    state = {"sent": [], "result": {}, "pending": []}

    async def send(message):
        m = message["message"]
        state["sent"].append(m)
        return state["result"].get(m.get("token") or m.get("topic"), fcm.SendResult.OK)

    monkeypatch.setattr(fcm, "is_enabled", lambda: True)
    monkeypatch.setattr(fcm, "send", send)
    monkeypatch.setattr(notification_service, "_spawn", state["pending"].append)

    def flush():
        coros, state["pending"][:] = state["pending"][:], []
        if coros:
            asyncio.run(_gather(coros))
        return state["sent"]

    state["flush"] = flush
    return state


async def _gather(coros):
    await asyncio.gather(*coros)


def register(client, mailbox_id, auth, token=TOKEN_A):
    return client.post(f"{P}/devices", json={"mailbox_id": mailbox_id, "platform": "fcm", "token": token},
                       headers=auth)


def fake_calendar(center_id, start, days):
    return [CalendarDay(date=start + timedelta(days=i), open=True, hours=[{"from": "09:00", "to": "17:00"}])
            for i in range(days)]


def test_register_requires_mailbox_key(client):
    mailbox_id, auth = new_mailbox(client)
    assert register(client, mailbox_id, {}).json()["code"] == "BAD_KEY"
    assert register(client, mailbox_id, auth).status_code == 204
    assert register(client, mailbox_id, auth).status_code == 204  # 重複 = 更新
    assert [d.token for d in devices_repo.all_devices()] == [TOKEN_A]


def test_token_moves_to_new_mailbox_and_unregister_is_scoped(client):
    mb1, auth1 = new_mailbox(client)
    mb2, auth2 = new_mailbox(client)
    register(client, mb1, auth1)
    register(client, mb2, auth2)  # 重灌 App 換信箱
    assert devices_repo.get(TOKEN_A).mailbox_id == mb2
    # 舊信箱刪不到別人的裝置
    client.request("DELETE", f"{P}/devices?mailbox_id={mb1}", json={"token": TOKEN_A}, headers=auth1)
    assert devices_repo.get(TOKEN_A) is not None
    res = client.request("DELETE", f"{P}/devices?mailbox_id={mb2}", json={"token": TOKEN_A}, headers=auth2)
    assert res.status_code == 204 and devices_repo.get(TOKEN_A) is None


def test_borrow_pushes_booked_to_all_devices(client, fake_fcm, monkeypatch):
    # 預約成功預設不推播；這裡把它加進推播清單，驗證文案與多裝置
    monkeypatch.setattr(config, "PUSH_EVENT_TYPES", {*config.PUSH_EVENT_TYPES, "reservation.booked"})
    monkeypatch.setattr(centers_service, "fetch_center_calendar", fake_calendar)
    signed_post(client, "/hooks/center/stock", {"event_id": "s1", "variant_id": "101", "stock": 1, "waiting": 0})
    mailbox_id, auth = new_mailbox(client)
    register(client, mailbox_id, auth, TOKEN_A)
    register(client, mailbox_id, auth, TOKEN_B)

    r = client.post(f"{P}/reservations", json=borrow_body(mailbox_id), headers={"Idempotency-Key": "p1"}).json()
    sent = fake_fcm["flush"]()

    assert {m["token"] for m in sent} == {TOKEN_A, TOKEN_B}
    m = sent[0]
    deadline = today() + timedelta(days=1)
    weekday = "一二三四五六日"[deadline.weekday()]
    assert m["notification"] == {"title": "預約成功",
                                 "body": f"請於 {deadline.month}/{deadline.day}（{weekday}） 前到合宜輔具中心取貨"}
    assert m["data"]["type"] == "reservation.booked"
    assert m["data"]["reservation_id"] == r["id"]
    assert set(m["data"]) == {"type", "event_id", "reservation_id"}  # 沒有 None 欄位
    assert all(isinstance(v, str) for v in m["data"].values())
    # 鎖定畫面不出現個資
    assert CONTACT["name"] not in str(m) and CONTACT["mobile"] not in str(m)


def test_only_async_events_are_pushed(client, fake_fcm):
    """通知只給非同步消息：到貨、取貨提醒、中心確認。使用者剛做的事不推播，但事件仍在信箱。"""
    from app.features.mailbox import service as mailbox_service

    mailbox_id, auth = new_mailbox(client)
    register(client, mailbox_id, auth)
    quiet = ("reservation.booked", "reservation.cancelled", "reservation.expired", "reservation.completed")
    for t in quiet:
        mailbox_service.append_event(mailbox_id, t, ref={"reservation_id": "B1"})
    assert fake_fcm["flush"]() == []

    loud = ("reservation.pickup_reminder", "reservation.confirmed")
    for t in loud:
        mailbox_service.append_event(mailbox_id, t, ref={"reservation_id": "B1"})
    assert [m["data"]["type"] for m in fake_fcm["flush"]()] == list(loud)

    events = client.get(f"{P}/mailboxes/{mailbox_id}/events?wait=0", headers=auth).json()["events"]
    assert [e["type"] for e in events] == [*quiet, *loud]


def test_stock_arrival_push_shows_device_name(client, fake_fcm, monkeypatch):
    from app.features.catalog import service as catalog_service

    monkeypatch.setattr(catalog_service, "fetch_catalog", lambda: [
        {"id": "1", "name": "輪椅類", "variants": [{"id": "101", "name": "電動輪椅"}]}])
    signed_post(client, "/hooks/center/stock", {"event_id": "s1", "variant_id": "101", "stock": 0, "waiting": 3})
    mailbox_id, auth = new_mailbox(client)
    register(client, mailbox_id, auth)
    client.post(f"{P}/subscriptions", json={"mailbox_id": mailbox_id, "variant_id": "101"}, headers=auth)

    signed_post(client, "/hooks/center/stock", {"event_id": "s2", "variant_id": "101", "stock": 1, "waiting": 2})
    (m,) = fake_fcm["flush"]()
    # 到貨通知依團隊決定顯示品項名稱（texts.py）
    assert m["notification"] == {"title": "到貨通知", "body": "你訂閱的「電動輪椅」已到貨，可以預約了"}
    assert m["data"]["variant_id"] == "101" and "reservation_id" not in m["data"]
    assert m["data"]["variant_name"] == "電動輪椅" and m["data"]["category_name"] == "輪椅類"
    subs = client.get(f"{P}/subscriptions", params={"mailbox_id": mailbox_id}, headers=auth).json()
    assert subs[0]["variant_name"] == "電動輪椅" and subs[0]["category_name"] == "輪椅類"


def test_invalid_token_is_removed(client, fake_fcm):
    mailbox_id, auth = new_mailbox(client)
    register(client, mailbox_id, auth)
    fake_fcm["result"][TOKEN_A] = fcm.SendResult.INVALID_TOKEN
    from app.features.mailbox import service as mailbox_service

    mailbox_service.append_event(mailbox_id, "reservation.confirmed", ref={"reservation_id": "B1"})
    fake_fcm["flush"]()
    assert devices_repo.get(TOKEN_A) is None


def test_temporary_failure_is_retried_then_dropped(client, fake_fcm):
    mailbox_id, auth = new_mailbox(client)
    register(client, mailbox_id, auth)
    fake_fcm["result"][TOKEN_A] = fcm.SendResult.RETRY
    from app.features.mailbox import service as mailbox_service

    mailbox_service.append_event(mailbox_id, "reservation.pickup_reminder", ref={"reservation_id": "B1"})
    fake_fcm["flush"]()
    assert len(notification_service._retry_queue) == 1
    asyncio.run(notification_service.retry_failed())
    assert len(notification_service._retry_queue) == 1  # 第 2 次
    asyncio.run(notification_service.retry_failed())
    assert notification_service._retry_queue == []  # 第 3 次失敗後放棄
    assert len(fake_fcm["sent"]) == 3


def test_notice_watch_pushes_only_new_notices_via_topic(client, fake_fcm, monkeypatch):
    mailbox_id, auth = new_mailbox(client)
    now = datetime(2026, 11, 7, 12, tzinfo=TAIPEI)
    notices = [{"id": "252", "title": "國慶連假休館公告", "published_at": now - timedelta(days=30),
                "ends_at": now + timedelta(days=30)}]
    monkeypatch.setattr(notice_watch, "fetch_notices", lambda: notices)

    assert asyncio.run(notice_watch.check_new_notices()) == 0  # 第一次只記住，不推播
    notices.append({"id": "260", "title": "11/20 系統維護", "center_ids": ["heyi"], "published_at": now,
                    "ends_at": now + timedelta(days=30)})
    notices.append({"id": "261", "title": "已結束的公告", "published_at": now, "ends_at": now - timedelta(days=1)})
    assert asyncio.run(notice_watch.check_new_notices()) == 1
    assert asyncio.run(notice_watch.check_new_notices()) == 0  # 不重複推

    (m,) = fake_fcm["flush"]()
    assert m["topic"] == "assistive-notice" and "token" not in m
    assert m["notification"] == {"title": "服務公告", "body": "11/20 系統維護"}
    # 也寫進信箱，App 打開時可補拉
    ev = client.get(f"{P}/mailboxes/{mailbox_id}/events?wait=0", headers=auth).json()["events"]
    assert [(e["type"], e["data"]["title"]) for e in ev] == [("service.notice", "11/20 系統維護")]


def test_without_fcm_push_is_logged_as_local(client, monkeypatch):
    """沒設定 Firebase：照樣走推播流程，push_log 記成 local（看得到推了什麼），事件也在信箱。"""
    from app.tools import db

    calls = []
    monkeypatch.setattr(notification_service, "_spawn", calls.append)
    mailbox_id, auth = new_mailbox(client)
    register(client, mailbox_id, auth)
    from app.features.mailbox import service as mailbox_service

    mailbox_service.append_event(mailbox_id, "reservation.confirmed", ref={"reservation_id": "B1"})
    asyncio.run(_gather(calls))
    row = db.query("SELECT result, type FROM push_log ORDER BY id DESC LIMIT 1")[0]
    assert (row["result"], row["type"]) == ("local", "reservation.confirmed")
    assert len(client.get(f"{P}/mailboxes/{mailbox_id}/events?wait=0", headers=auth).json()["events"]) == 1


@pytest.mark.parametrize("status, body, expected", [
    (200, {"name": "projects/p/messages/1"}, fcm.SendResult.OK),
    (404, {"error": {"status": "NOT_FOUND"}}, fcm.SendResult.INVALID_TOKEN),
    (400, {"error": {"status": "INVALID_ARGUMENT"}}, fcm.SendResult.INVALID_TOKEN),
    (403, {"error": {"status": "PERMISSION_DENIED"}}, fcm.SendResult.FAILED),
    (429, {"error": {"status": "RESOURCE_EXHAUSTED"}}, fcm.SendResult.RETRY),
    (503, {}, fcm.SendResult.RETRY),
])
def test_fcm_http_v1_result_mapping(monkeypatch, status, body, expected):
    import httpx

    from app.config import get_settings

    seen = {}

    def handler(request):
        seen["url"], seen["auth"] = str(request.url), request.headers["authorization"]
        return httpx.Response(status, json=body)

    async def token():
        return "oauth-token"

    monkeypatch.setattr(get_settings(), "fcm_project_id", "townpass-test")
    monkeypatch.setattr(get_settings(), "fcm_credentials_file", "/dev/null")
    monkeypatch.setattr(fcm, "_access_token", token)
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    monkeypatch.setattr(fcm, "get_http_client", lambda: client)

    msg = fcm.build_message(title="t", body="b", data={"type": "x", "variant_id": None}, token=TOKEN_A)
    assert msg["message"]["data"] == {"type": "x"}
    assert asyncio.run(fcm.send(msg)) == expected
    assert seen["url"] == "https://fcm.googleapis.com/v1/projects/townpass-test/messages:send"
    assert seen["auth"] == "Bearer oauth-token"
