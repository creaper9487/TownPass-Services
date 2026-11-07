"""統一設定檔。所有功能開關、時間間隔都在這裡。

分兩種：
    1. Env（最上面）：從 .env 讀。只放「每台電腦不一樣」或「機密」的值。
    2. 其他（下面的大寫常數）：直接改這個檔案，不從 .env 讀，改完重開 server。

程式裡：
    from app.config import get_settings      → get_settings().host、get_settings().test_mode …（.env 的值）
    from app import config                   → config.API_ENABLED、config.STOCK_SYNC_SECONDS …（這個檔案的值）
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


# =====================================================================
# 1. 從 .env 讀（只有這幾個）
# =====================================================================
class Env(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # server 聽的 IP / port；同 Wi-Fi 的隊友打這個 IP。換網路 IP 會變，改 .env 就好
    host: str = "192.168.88.208"
    port: int = 8000

    # 測試模式：爬蟲改用固定假資料（不連官網）、開放 /_test/* 測試 API 與測試面板。正式環境一定要 false
    test_mode: bool = False

    # 本機 SQLite（推播裝置、推播紀錄）
    db_path: str = "data/local.db"

    # 背景工作（庫存同步、逾期掃描、送件、推播檢查）。跑 pytest 時關掉
    enable_background_jobs: bool = True

    # ---- 機密：不要 commit ----
    hook_secret: str = "dev-hook-secret"  # 中心 webhook 的 HMAC 密鑰
    fcm_project_id: str = ""  # Firebase 專案 ID；空的 = 推播只記錄在本機
    fcm_credentials_file: str = ""  # Firebase 服務帳號金鑰 JSON 路徑


@lru_cache
def get_settings() -> Env:
    return Env()


# =====================================================================
# 2. 直接改這裡
# =====================================================================
APP_NAME = "Taipei Codefest 2026 Backend"
DEBUG = False
API_PREFIX = "/assistive/v1"
CORS_ORIGINS = ["*"]

# ---- API 開關：False = 整組 API 不註冊（打了回 404）----
API_ENABLED = {
    "health": True,  # GET /health
    "catalog": True,  # GET /catalog
    "centers": True,  # GET /centers、/centers/{id}/calendar
    "stock": True,  # GET /stock
    "mailboxes": True,  # /mailboxes（信箱、事件、SSE、ack）
    "devices": True,  # /devices（推播裝置登記）
    "reservations": True,  # /reservations（建立、取消、批次查詢）
    "subscriptions": True,  # /subscriptions（到貨通知）
    "hooks": True,  # /hooks/center/*（中心回呼）
    "test": True,  # /_test/*（測試 API 與測試面板）；另外還要 .env 的 TEST_MODE=true 才會開
}

# ---- 背景排程間隔 ----
# 庫存同步：每次約 13 個請求打官網，規格的 30–60 秒太頻繁，先用 3 分鐘；正式上線前跟中心確認
STOCK_SYNC_SECONDS = 180
EXPIRE_SCAN_SECONDS = 60  # 逾期自動取消、取貨提醒（規格：逾期後 ≤ 1 分鐘）
FORWARD_RETRY_SECONDS = 30  # 送件佇列重試
PUSH_CHECK_MINUTES = 5  # 檢查官網新公告 → 推播；重試失敗的推播

# ---- 推播 ----
FCM_NOTICE_TOPIC = "assistive-notice"  # 公告用 topic，App 啟動時要訂閱
MAX_DEVICES_PER_MAILBOX = 10

# ---- 中心 webhook ----
HOOK_MAX_SKEW_SECONDS = 300  # X-Timestamp 允許誤差 5 分鐘


def test_api_enabled() -> bool:
    """測試 API / 測試面板要同時：config 開著 + .env TEST_MODE=true。"""
    return API_ENABLED.get("test", False) and get_settings().test_mode
