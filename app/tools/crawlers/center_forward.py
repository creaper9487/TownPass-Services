from app.tools.crawlers.schemas import ForwardReceipt


def forward_reservation(payload: dict) -> ForwardReceipt:
    """把一筆預約（含個資）送到負責的輔具中心。

    ⚠ 這裡會拿到個資：不要 print、不要寫 log、不要存檔。

    資料來源 / 目的地：
        官方系統 https://tpap.gov.taipei/app37 只有網頁表單（帶 CSRF token SYNCHRONIZER_TOKEN），
        沒有公開 API。目前預設做法是「我們的系統當紀錄主體，中心用極簡後台收件」，
        所以這裡可能是：
            a. 中心提供 API 後，直接呼叫它；或
            b. 寫進中心後台 / 寄信給中心；或
            c. （需取得中心同意）模擬官網表單送出。
        在確定介接方式前先保持 NotImplementedError，送件會留在佇列裡重試（最多 24 小時）。

    參數 payload（就是 POST /reservations 的內容）：
        {
            "reservation_id": "B202611073703",
            "service": "borrow" | "assess" | "repair" | "recycle",
            "center_id": "heyi" | "south" | "west",
            "items": ["101"]  或官方勾選項目字串,
            "other_text": "…" | None,
            "contact": {"name", "mobile", "phone", "gender", "email"},
            "subject": {"name", "id_no", "registered_district", "living_county",
                        "living_district", "remark"} | None,   # 評估、維修才有
            "pickup":  {"district", "address", "has_elevator",
                        "need_certificate", "remark"} | None    # 回收才有
        }

    需要的功能：
        1. 送出成功回 accepted=True，若中心有單號放 center_reference。
        2. 暫時性失敗（網路、5xx）直接 raise Exception，後端會重試。
        3. 永久失敗（資料被拒）回 accepted=False，message 寫原因（不要含個資）。

    回傳：
        ForwardReceipt，範例：{"accepted": true, "center_reference": "A12345", "message": null}
    """
    raise NotImplementedError("forward_reservation 尚未實作")
