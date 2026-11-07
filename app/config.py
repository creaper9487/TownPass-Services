"""應用程式設定，從環境變數或 .env 讀取。"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Taipei Codefest 2026 Backend"
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

    # 中心回呼 webhook 與推播閘道共用的 HMAC 密鑰
    hook_secret: str = "dev-hook-secret"
    hook_max_skew_seconds: int = 300  # X-Timestamp 允許誤差 5 分鐘

    # 台北通推播閘道；空字串 = 尚未開通，只靠 pull
    push_gateway_url: str = ""
    push_secret: str = "dev-push-secret"


@lru_cache
def get_settings() -> Settings:
    return Settings()
