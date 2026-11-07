from app.tools.crawlers.schemas import ForwardReceipt


def forward_reservation(payload: dict) -> ForwardReceipt:
    """【做什麼】把使用者填好的預約（含個資）送到負責的臺北市輔具中心。
    這個不是爬蟲，是「送出去」。介接方式還沒跟中心談定，先不用寫。

    ⚠ payload 裡有姓名、電話、身分證、地址：不要 print、不要寫 log、不要存檔。

    ─────────────────────────────────────────
    目的地（三選一，等中心回覆再決定）
        a. 中心提供 API → 直接呼叫
        b. 寫進中心用的極簡後台 / 寄 email 給中心
        c. （要先取得中心同意）模擬官網表單送出：
           https://tpap.gov.taipei/app37 的表單帶 CSRF token（SYNCHRONIZER_TOKEN），
           要先 GET 表單頁拿 token 和 cookie，再 POST。
        還沒決定前保持 NotImplementedError：預約會留在佇列裡，最多 24 小時後丟棄。

    ─────────────────────────────────────────
    參數 payload（就是使用者送進 POST /reservations 的內容，只會是臺北市）
        {
            "reservation_id": "B202611073703",
            "service": "borrow" | "assess" | "repair" | "recycle",
                       借用       評估       維修       回收
            "center_id": "heyi" | "south" | "west",
            "items": ["101"]（借用：品項代碼）或 ["輪椅"]（其他：官方表單勾選項目）,
            "other_text": "「其他」輔具說明" | None,
            "contact": {"name", "mobile", "phone", "gender", "email"},       # 聯絡人
            "subject": {"name", "id_no", "registered_district",               # 輔具使用者
                        "living_district", "remark"} | None,                  # 只有評估、維修
            "pickup":  {"district", "address", "has_elevator",                # 回收地點
                        "need_certificate", "remark"} | None                  # 只有回收
        }

    ─────────────────────────────────────────
    回傳（ForwardReceipt）
        | 情況                       | 怎麼回                                                    |
        |----------------------------|-----------------------------------------------------------|
        | 中心收到了                 | {"accepted": true, "center_reference": "中心單號或 None"} |
        | 中心拒收（資料有問題）     | {"accepted": false, "message": "原因（不要放個資）"}      |
        | 暫時失敗（斷線、5xx）      | 直接 raise Exception，後端會自動重試                      |
    """
    raise NotImplementedError("forward_reservation 尚未實作")
