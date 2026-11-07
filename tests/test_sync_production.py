"""正式模式：python -m app.cli sync 直接跑「抓資料 → 更新到貨訂閱 → 推播」，不需要 server、不需要測試模式；
預設不產生任何模擬公告 / 模擬到貨。"""

import asyncio

from app.cli import main as cli
from app.config import get_settings
from app.features import jobs
from app.features.devices import service as devices_service
from app.features.mailbox import service as mailbox_service
from app.features.notification import notice_watch
from app.features.stock import service as stock_service
from app.features.subscription import service as subscription_service
from app.features.subscription.schemas import SubscriptionCreate
from app.tools import db


def test_default_test_mode_makes_no_fake_notices_or_arrivals(monkeypatch):
    monkeypatch.setattr(get_settings(), "test_mode", True)
    for _ in range(6):
        r = asyncio.run(jobs.sync_now())
        assert r["new_notices"] == 0
    assert not db.query("SELECT 1 FROM events WHERE type = 'service.notice'")


def test_cli_sync_in_production_mode_pushes_real_arrival(monkeypatch, capsys):
    assert get_settings().test_mode is False
    stock = [{"variant_id": "185", "stock": 0, "waiting": 3}]
    monkeypatch.setattr(stock_service, "fetch_stock", lambda: stock)  # 官網爬蟲（這裡用固定值代替）
    monkeypatch.setattr(subscription_service.catalog_service, "fetch_catalog",
                        lambda: [{"id": "1", "name": "輪椅", "variants": [{"id": "185", "name": "輪椅"}]}])
    asyncio.run(jobs.sync_now())

    mb = mailbox_service.create()
    devices_service.register(mb.mailbox_id, "fcm", "local-real-phone")
    sub_id = asyncio.run(subscription_service.create(SubscriptionCreate(mailbox_id=mb.mailbox_id, variant_id="185")))

    cli(["sync"])  # 官網沒變：不推
    assert db.query("SELECT status FROM subscriptions WHERE id = ?", (sub_id,))[0]["status"] == "waiting"

    stock[0] = {"variant_id": "185", "stock": 1, "waiting": 2}  # 官網到貨了
    cli(["sync"])
    out = capsys.readouterr().out
    assert "正式模式（官網資料）" in out
    assert "stock.arrived" in out and f"信箱 {mb.mailbox_id}" in out
    assert db.query("SELECT status FROM subscriptions WHERE id = ?", (sub_id,))[0]["status"] == "arrived"


def test_cli_sync_reports_crawler_problems_instead_of_crashing(monkeypatch, capsys):
    def broken():
        raise ConnectionError("官網連不到")

    monkeypatch.setattr(stock_service, "fetch_stock", broken)
    cli(["sync"])
    out = capsys.readouterr().out
    assert "stock: ConnectionError" in out


def test_seen_notices_are_persisted(monkeypatch):
    notices = [{"id": "n1", "title": "舊公告", "published_at": "2026-11-01T00:00:00+08:00"}]
    monkeypatch.setattr(notice_watch, "fetch_notices", lambda: notices)
    assert asyncio.run(notice_watch.check_new_notices()) == 0  # 第一次只記住
    notices.append({"id": "n2", "title": "新公告", "published_at": "2026-11-07T00:00:00+08:00"})
    assert asyncio.run(notice_watch.check_new_notices()) == 1
    # 換一個 process（CLI / 重啟）一樣不會重推
    assert asyncio.run(notice_watch.check_new_notices()) == 0
    assert {r["id"] for r in db.query("SELECT id FROM notice_seen")} == {"n1", "n2"}
