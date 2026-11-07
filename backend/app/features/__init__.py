"""商業邏輯層。每個 feature 一個資料夾：

    schemas.py     API 輸入 / 輸出的 Pydantic model
    repository.py  資料存取（目前是記憶體，之後換資料庫只改這裡）
    service.py     商業邏輯；不碰 HTTP（Request / Response），只 raise AppError

分層：routers（HTTP）→ features/*/service（邏輯）→ repository（資料）/ tools（爬蟲、工具）
"""
