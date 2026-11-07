"""欄位 / 服務 / 品項規則來自 config；不存在的品項要擋；資料存在 SQLite，重啟還在。"""

import pytest

from app import config
from app.config import get_settings
from app.tools import db
from tests.test_api import CONTACT, P, new_mailbox, signed_post

SUBJECT = {"name": "王小明", "id_no": "A123456789", "registered_district": "大安區",
           "living_county": "臺北市", "living_district": "大安區"}


@pytest.fixture
def test_mode(monkeypatch):
    monkeypatch.setattr(get_settings(), "test_mode", True)


def post(client, body, key="k"):
    return client.post(f"{P}/reservations", json=body, headers={"Idempotency-Key": key})


def test_subscribe_unknown_variant_rejected(client, test_mode):
    mb, auth = new_mailbox(client)
    res = client.post(f"{P}/subscriptions", json={"mailbox_id": mb, "variant_id": "NOPE-999"}, headers=auth)
    assert res.status_code == 422 and res.json()["fields"] == ["variant_id"]
    ok = client.post(f"{P}/subscriptions", json={"mailbox_id": mb, "variant_id": "181"}, headers=auth)
    assert ok.status_code == 201


def test_subscribe_unknown_variant_rejected_without_catalog(client):
    """目錄爬蟲壞掉時，退而查庫存表。"""
    mb, auth = new_mailbox(client)
    res = client.post(f"{P}/subscriptions", json={"mailbox_id": mb, "variant_id": "NOPE"}, headers=auth)
    assert res.status_code == 422
    signed_post(client, "/hooks/center/stock", {"event_id": "e", "variant_id": "NOPE", "stock": 0, "waiting": 1})
    assert client.post(f"{P}/subscriptions", json={"mailbox_id": mb, "variant_id": "NOPE"},
                       headers=auth).status_code == 201


def test_borrow_unknown_or_duplicate_items_rejected(client, test_mode):
    mb, _ = new_mailbox(client)
    body = {"service": "borrow", "mailbox_id": mb, "center_id": "heyi", "items": ["NOPE"], "contact": CONTACT}
    res = post(client, body).json()
    assert res["code"] == "INVALID_FIELD" and res["fields"] == ["items"]  # 不是 OUT_OF_STOCK
    body["items"] = ["182", "182"]
    assert post(client, body, "k4").json()["fields"] == ["items"]


def test_blocked_variant_and_category_from_config(client, test_mode, monkeypatch):
    monkeypatch.setattr(config, "BLOCKED_VARIANTS", ["181"])
    monkeypatch.setattr(config, "BORROW_CATEGORIES", ["1", "2"])
    cats = client.get(f"{P}/catalog").json()["categories"]
    assert [c["id"] for c in cats] == ["1", "2"]
    assert "181" not in {v["id"] for c in cats for v in c["variants"]}
    assert "181" not in client.get(f"{P}/stock").json()["items"]
    mb, auth = new_mailbox(client)
    for vid in ("181", "200"):  # 181 封鎖、200 在第 3 類以後
        res = client.post(f"{P}/subscriptions", json={"mailbox_id": mb, "variant_id": vid}, headers=auth)
        assert res.status_code == 422, vid


def test_other_services_items_follow_config(client, monkeypatch):
    mb, _ = new_mailbox(client)
    body = {"service": "repair", "mailbox_id": mb, "items": ["手動輪椅"], "contact": CONTACT, "subject": SUBJECT}
    assert post(client, body, "a").status_code == 201
    body["items"] = ["飛機"]
    assert post(client, body, "b").json()["fields"] == ["items"]
    body["items"] = ["其他"]
    assert post(client, body, "c").json()["fields"] == ["other_text"]
    body["other_text"] = "特製坐墊"
    assert post(client, body, "d").status_code == 201
    # 少了必填欄位組
    assert post(client, {**body, "subject": None}, "e").json()["fields"] == ["subject"]
    # 關掉服務
    monkeypatch.setitem(config.SERVICES, "repair", {**config.SERVICES["repair"], "enabled": False})
    assert post(client, body, "f").json()["fields"] == ["service"]
    assert client.get(f"{P}/forms/repair").status_code == 404


def test_field_rules_come_from_config(client, monkeypatch):
    """改 config.FIELDS 後重新建立 schema，驗證規則跟著變（不寫死）。"""
    from app.tools.fields import field, field_type
    from pydantic import BaseModel, ValidationError

    monkeypatch.setitem(config.FIELDS, "contact.name", {"required": True, "max_length": 3, "label": "姓名"})

    class C(BaseModel):
        name: field_type("contact.name") = field("contact.name")

    C(name="王小明")
    with pytest.raises(ValidationError):
        C(name="王小明明")


def test_forms_endpoint(client):
    f = client.get(f"{P}/forms/recycle").json()
    assert f["item_options"][-1] == "其他" and f["allow_other"] is True
    assert "pickup.address" in f["required_fields"] and "contact.mobile" in f["required_fields"]
    assert "subject.id_no" not in f["required_fields"]
    assert len(f["districts"]) == 12 and f["fields"]["contact.mobile"]["pattern"]
    assert client.get(f"{P}/forms/borrow").json()["required_fields"][:2] == ["items", "center_id"]
    assert client.get(f"{P}/forms/nope").status_code == 404


def test_no_forwarding_and_no_personal_data_stored(client, test_mode):
    mb, _ = new_mailbox(client)
    r = client.post(f"{P}/_test/scenario", json={}).json()
    rows = db.query("SELECT * FROM reservations WHERE id = ?", (r["reservation"]["id"],))
    assert rows[0]["forward_state"] == "off"
    dump = str([dict(x) for x in db.query("SELECT * FROM reservations")])
    assert "測試使用者" not in dump and "0900000000" not in dump


def test_data_survives_restart(tmp_path, monkeypatch):
    """DB 換成檔案、關掉再開，信箱 / 預約 / 庫存 / 訂閱都還在。"""
    from fastapi.testclient import TestClient

    from app.main import create_app

    monkeypatch.setattr(get_settings(), "db_path", str(tmp_path / "t.db"))
    monkeypatch.setattr(get_settings(), "test_mode", True)
    db.close()
    try:
        c = TestClient(create_app())
        r = c.post(f"{P}/_test/scenario", json={}).json()
        auth = {"Authorization": f"Bearer {r['mailbox_key']}"}
        c.post(f"{P}/subscriptions", json={"mailbox_id": r["mailbox_id"], "variant_id": "200"}, headers=auth)
        version = c.get(f"{P}/stock").json()["version"]

        db.close()  # 模擬重啟

        c = TestClient(create_app())
        got = c.post(f"{P}/reservations:batchGet",
                     json=[{"id": r["reservation"]["id"], "access_key": r["reservation"]["access_key"]}]).json()
        assert got[0]["status"] == "booked"
        assert c.get(f"{P}/stock").json()["version"] == version
        ev = c.get(f"{P}/mailboxes/{r['mailbox_id']}/events?wait=0", headers=auth).json()["events"]
        assert [e["type"] for e in ev] == ["reservation.booked"]
        assert len(db.query("SELECT * FROM subscriptions")) == 1
    finally:
        db.close()
        monkeypatch.undo()
        db.close()
