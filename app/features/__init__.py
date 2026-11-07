"""各功能模組（商業邏輯）。每個 feature 一個資料夾：

    features/<name>/
        schemas.py   # Pydantic 輸入 / 輸出模型
        service.py   # 商業邏輯，不依賴 FastAPI request 物件
"""
