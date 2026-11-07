"""應用程式設定，從環境變數或 .env 讀取。"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Taipei Codefest 2026 Backend"

    # python app/main.py 啟動時聽的 IP / port（區網內手機、前端用這個連）
    host: str = "192.168.88.208"
    port: int = 8000

    # 測試模式：爬蟲改回傳固定假資料（不連官網），並開放 /_test/* 測試 API。正式環境一定要 false。
    test_mode: bool = False
    # 本機 SQLite（推播裝置、推播紀錄）
    db_path: str = "data/local.db"
    debug: bool = False
    api_prefix: str = "/assistive/v1"
    cors_origins: list[str] = ["*"]

    # 背景工作（庫存同步、逾期掃描、送件佇列）。測試時關掉。
    enable_background_jobs: bool = True
    # 每次同步約 13 個請求打官網（分類頁 + 每個分類 1 頁），規格的 30–60 秒太頻繁；
    # 先用 3 分鐘，正式上線前跟輔具中心確認可接受的頻率。前端每 10 秒輪詢的是我們的後端，不受影響。
    stock_sync_seconds: int = 180
    expire_scan_seconds: int = 60  # 規格：逾期後 ≤ 1 分鐘自動取消
    forward_retry_seconds: int = 30

    # 中心回呼 webhook 的 HMAC 密鑰
    hook_secret: str = "dev-hook-secret"
    hook_max_skew_seconds: int = 300  # X-Timestamp 允許誤差 5 分鐘

    # 推播（FCM）。兩個都設定才會真的發；沒設定時事件只寫進信箱。
    fcm_project_id: str = ""
    fcm_credentials_file: str = ""  # 服務帳號金鑰 JSON 路徑，不要 commit
    fcm_notice_topic: str = "assistive-notice"  # 公告用 topic，App 啟動時訂閱
    max_devices_per_mailbox: int = 10

    # 每幾分鐘檢查一次：官網新公告 → 推播 service.notice、重試失敗的推播
    push_check_minutes: int = 5


@lru_cache
def get_settings() -> Settings:
    return Settings()
