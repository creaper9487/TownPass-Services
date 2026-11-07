"""共用工具。

- crawlers/   爬蟲與外部資料來源（給爬蟲組實作，格式見 crawlers/schemas.py）
- exceptions  錯誤碼與 problem+json
- security    密鑰產生、hash、HMAC 簽章
- districts   行政區 → 服務中心對照
- push        推播閘道（只送 mailbox_id 與 cursor）
- timeutil    台北時間
- http_client 共用 httpx client
- logger
"""
