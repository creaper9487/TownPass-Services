# taipei-codefest-2026-Backend

FastAPI 後端。

## 專案結構

```
app/
├── main.py            # 進入點：建立 app、CORS、exception handler、掛 routers
├── config.py          # 設定（讀取環境變數 / .env）
├── routers/           # HTTP 層：定義 endpoint，呼叫 features
│   ├── __init__.py    # api_router，集中 include 所有 router
│   ├── health.py
│   └── example.py
├── features/          # 商業邏輯，一個功能一個資料夾
│   └── example/
│       ├── schemas.py # Pydantic models
│       └── service.py # 邏輯實作
└── tools/             # 共用工具
    ├── logger.py
    ├── response.py    # 統一回應格式 ApiResponse / ok / fail
    ├── exceptions.py  # AppError、NotFoundError、全域 handler
    └── http_client.py # 共用 httpx AsyncClient
tests/
```

## 新增一個功能

1. 建立 `app/features/<name>/schemas.py`、`service.py`
2. 建立 `app/routers/<name>.py`，呼叫 service
3. 在 `app/routers/__init__.py` 中 `include_router`

## 開發

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

API 文件：http://localhost:8000/docs

測試：

```bash
pytest
```
