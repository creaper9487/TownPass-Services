"""config.CHECK_OPENING_HOURS：關掉 = 不管中心有沒有開都能預約；打開 = 照行事曆。"""

import asyncio
from datetime import date, datetime, timedelta

from app import config
from app.features.centers import service as centers_service
from app.features.reservation import service as reservation_service
from app.tools import db
from app.tools.crawlers.schemas import CalendarDay
from app.tools.timeutil import TAIPEI
from tests.test_api import P, borrow_body, new_mailbox, signed_post


def all_closed(center_id, start, days):
    return [CalendarDay(date=start + timedelta(days=i), open=False, reason="例假日休館") for i in range(days)]


def setup(client, monkeypatch):
    monkeypatch.setattr(centers_service, "fetch_center_calendar", all_closed)
    monkeypatch.setattr(reservation_service, "today", lambda: date(2026, 11, 7))  # 週六
    signed_post(client, "/hooks/center/stock", {"event_id": "s", "variant_id": "101", "stock": 2, "waiting": 0})
    mb, auth = new_mailbox(client)
    return mb, auth


def test_default_ignores_opening_hours(client, monkeypatch):
    assert config.CHECK_OPENING_HOURS is False
    mb, _ = setup(client, monkeypatch)
    r = client.post(f"{P}/reservations", json=borrow_body(mb), headers={"Idempotency-Key": "a"})
    assert r.status_code == 201, r.text
    assert r.json()["pickup"] == {"deadline": "2026-11-08", "open_dates": ["2026-11-07", "2026-11-08"]}


def test_pickup_days_from_config(client, monkeypatch):
    monkeypatch.setattr(config, "PICKUP_DAYS", 3)
    mb, _ = setup(client, monkeypatch)
    r = client.post(f"{P}/reservations", json=borrow_body(mb), headers={"Idempotency-Key": "b"}).json()
    assert r["pickup"]["deadline"] == "2026-11-09" and len(r["pickup"]["open_dates"]) == 3


def test_check_on_rejects_when_center_closed(client, monkeypatch):
    monkeypatch.setattr(config, "CHECK_OPENING_HOURS", True)
    mb, _ = setup(client, monkeypatch)
    r = client.post(f"{P}/reservations", json=borrow_body(mb), headers={"Idempotency-Key": "c"})
    assert r.status_code == 422 and r.json()["code"] == "PICKUP_WINDOW_CLOSED"


def test_reminders_use_config_times_when_check_off(client, monkeypatch):
    mb, auth = setup(client, monkeypatch)
    rid = client.post(f"{P}/reservations", json=borrow_body(mb), headers={"Idempotency-Key": "d"}).json()["id"]
    from app.features.reservation import repository as repo

    row = repo.get(rid)
    row.pickup_deadline = date(2026, 11, 8)
    repo.save(row)

    def run_at(hh, mm):
        monkeypatch.setattr(reservation_service, "now", lambda: datetime(2026, 11, 8, hh, mm, tzinfo=TAIPEI))
        asyncio.run(reservation_service.send_pickup_reminders())
        return len(db.query("SELECT 1 FROM events WHERE type = 'reservation.pickup_reminder'"))

    assert run_at(8, 0) == 0
    assert run_at(9, 5) == 1  # 09:00
    assert run_at(10, 0) == 1  # 同一個時段不重複
    assert run_at(15, 1) == 2  # 15:00（中心休館也照樣提醒，因為不管開館）
