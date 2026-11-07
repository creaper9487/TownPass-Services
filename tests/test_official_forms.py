"""評估／維修的項目名稱要和官網表單一字不差（前端畫面是官網原文，送出的就是這些字）。"""

from app import config
from app.tools.crawlers.forms import parse_form_options
from tests.test_api import CONTACT, P, new_mailbox
from tests.test_config_rules import SUBJECT, post

# 官網 https://tpap.gov.taipei/app37/otherReserveView/index（2026-11-07）
OFFICIAL_ASSESS = ["居家用照顧床(病床)", "氣墊床", "輪椅座墊", "手動輪椅", "電動輪椅", "居家無障礙",
                   "矯具/義具", "視障輔具", "溝通輔具", "電腦輔具", "爬梯機借用"]
OFFICIAL_REPAIR = ["居家用照顧床(病床)", "氣墊床", "輪椅座墊", "手動輪椅", "電動輪椅", "拐杖/助行器", "便盆椅"]

FORM_HTML = """
<form>
  <label>申請評估</label>
  <label>居家用照顧床(病床)</label><label>氣墊床</label><label>電動輪椅</label><label>其他</label>
  <label>申請維修</label>
  <label>輪椅座墊</label><label> 拐杖/助行器
  </label><label>其他</label>
  <label>§聯絡人資料</label><label>*姓名</label>
</form>
"""


def test_config_matches_official_labels():
    assert config.SERVICES["assess"]["item_options"] == OFFICIAL_ASSESS
    assert config.SERVICES["repair"]["item_options"] == OFFICIAL_REPAIR
    # 官網沒有限制勾選幾項：全部項目都勾 + 其他也要收得下
    assert config.SERVICES["assess"]["max_items"] >= len(OFFICIAL_ASSESS) + 1
    assert config.SERVICES["repair"]["max_items"] >= len(OFFICIAL_REPAIR) + 1


def test_forms_endpoint_returns_official_labels(client):
    assert client.get(f"{P}/forms/assess").json()["item_options"] == OFFICIAL_ASSESS + ["其他"]
    assert client.get(f"{P}/forms/repair").json()["item_options"] == OFFICIAL_REPAIR + ["其他"]


def test_every_official_label_is_accepted_and_old_ones_rejected(client):
    mb, _ = new_mailbox(client)
    for service, labels in (("assess", OFFICIAL_ASSESS), ("repair", OFFICIAL_REPAIR)):
        for i, label in enumerate(labels):
            body = {"service": service, "mailbox_id": mb, "items": [label], "contact": CONTACT, "subject": SUBJECT}
            assert post(client, body, f"{service}-{i}").status_code == 201, label
        everything = {"service": service, "mailbox_id": mb, "items": labels + ["其他"], "other_text": "特製",
                      "contact": CONTACT, "subject": SUBJECT}
        assert post(client, everything, f"{service}-all").status_code == 201
    bad = {"service": "assess", "mailbox_id": mb, "items": ["輪椅"], "contact": CONTACT, "subject": SUBJECT}
    assert post(client, bad, "old-label").json()["fields"] == ["items"]


def test_parse_form_options():
    assert parse_form_options(FORM_HTML) == {
        "assess": ["居家用照顧床(病床)", "氣墊床", "電動輪椅"],
        "repair": ["輪椅座墊", "拐杖/助行器"],
    }
