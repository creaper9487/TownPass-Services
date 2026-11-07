"""官網「申請評估／申請維修」表單的勾選項目。

這不是 API 在用的爬蟲：後端驗證與 GET /forms/{service} 讀的是 config.SERVICES，不會在執行時連官網。
這支只用來對照——官網改了項目名稱，用 `python -m app.tools.crawlers.check forms` 就看得出 config 該改哪裡。

網址：https://tpap.gov.taipei/app37/otherReserveView/index
頁面是伺服器直接產生的 HTML：一張表單，先列「申請評估」的勾選項，再列「申請維修」的，最後是 §聯絡人資料。
"""

import requests
from bs4 import BeautifulSoup

FORM_URL = "https://tpap.gov.taipei/app37/otherReserveView/index"
OTHER = "其他"  # 官網每組最後都有「其他」；後端用 allow_other 處理，不放進 item_options


def parse_form_options(html: str) -> dict[str, list[str]]:
    """從表單 HTML 取出 {"assess": [...], "repair": [...]}（不含「其他」）。"""
    labels = [" ".join(label.get_text().split()) for label in BeautifulSoup(html, "html.parser").find_all("label")]
    groups = {"申請評估": "assess", "申請維修": "repair"}
    out: dict[str, list[str]] = {}
    current: str | None = None
    for text in labels:
        if text in groups:
            current = groups[text]
            out[current] = []
        elif text.startswith("§"):  # §聯絡人資料：勾選項到這裡結束
            current = None
        elif current and text and text != OTHER:
            out[current].append(text)
    return out


def fetch_form_options() -> dict[str, list[str]]:
    res = requests.get(FORM_URL, params={"lang": "zh_TW"}, timeout=20)
    res.raise_for_status()
    return parse_form_options(res.text)
