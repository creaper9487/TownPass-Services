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

# =====================================================================
# 服務與欄位定義：API 驗證、GET /forms/{service} 都直接讀這裡，不寫死在程式裡
# 改完重開 server 就生效
# =====================================================================

TAIPEI_DISTRICTS = ["中正區", "大同區", "中山區", "松山區", "大安區", "萬華區",
                    "信義區", "士林區", "北投區", "內湖區", "南港區", "文山區"]

# ---- 支援哪些服務 ----
#   enabled      False = 這個服務不收（POST /reservations 回 422 INVALID_FIELD）
#   groups       這個服務要填哪幾組欄位（對應下面 FIELDS 的前綴）
#   item_options 可勾選的項目（items 只能從這裡選）；None = 借用，items 是品項代碼
#   allow_other  可不可以選「其他」並填 other_text
#   max_items    items 最多幾個
SERVICES = {
    "borrow": {"enabled": True, "label": "二手輔具借用", "groups": ["contact"], "item_options": None,
               "allow_other": False, "max_items": 3},
    "assess": {"enabled": True, "label": "輔具評估", "groups": ["contact", "subject"],
               "item_options": ["輪椅", "電動輪椅", "助行器", "拐杖", "洗澡椅", "便盆椅", "居家照顧床", "移位輔具",
                                "擺位輔具", "電動代步車", "輔助溝通", "視覺輔具"],
               "allow_other": True, "max_items": 5},
    "repair": {"enabled": True, "label": "輔具維修", "groups": ["contact", "subject"],
               "item_options": ["輪椅", "電動輪椅", "助行器", "居家照顧床", "電動代步車"],
               "allow_other": True, "max_items": 5},
    "recycle": {"enabled": True, "label": "輔具回收", "groups": ["contact", "pickup"],
                "item_options": ["輪椅", "助行器", "拐杖", "洗澡椅", "便盆椅", "居家照顧床"],
                "allow_other": True, "max_items": 10},
}
# 上面 assess / repair / recycle 的 item_options 是暫定的，要對照官方表單的勾選項目再改

# ---- 支援哪些借用品項（GET /catalog、借用、到貨通知都會套用）----
BORROW_CATEGORIES: list[str] | None = None  # None = 全部分類；例如 ["1", "2"] 只開放這兩類
BLOCKED_VARIANTS: list[str] = []  # 不開放的品項代碼，例如 ["185"]

# ---- 欄位規則 ----
#   required  必填        min_length / max_length  字數
#   pattern   格式（正規表示式）                    choices  只能選這些
#   type      預設 str；也可以是 bool
FIELDS = {
    "contact.name": {"required": True, "min_length": 1, "max_length": 50, "label": "聯絡人姓名"},
    "contact.mobile": {"required": True, "pattern": r"^09\d{8}$", "label": "手機"},
    "contact.phone": {"required": False, "max_length": 20, "pattern": r"^[0-9#\-() ]*$", "label": "市話"},
    "contact.gender": {"required": True, "choices": ["M", "F", "X"], "label": "性別"},
    "contact.email": {"required": False, "max_length": 100, "pattern": r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
                      "label": "E-mail"},

    "subject.name": {"required": True, "min_length": 1, "max_length": 50, "label": "使用者姓名"},
    "subject.id_no": {"required": True, "pattern": r"^[A-Z][0-9A-Z]\d{8}$", "label": "身分證字號"},
    "subject.registered_district": {"required": True, "choices": TAIPEI_DISTRICTS, "label": "戶籍行政區"},
    "subject.living_county": {"required": True, "max_length": 10, "label": "居住縣市"},  # 非臺北市 → NOT_ELIGIBLE
    "subject.living_district": {"required": True, "max_length": 10, "label": "居住行政區"},
    "subject.remark": {"required": False, "max_length": 500, "label": "備註 / 維修需求"},

    "pickup.district": {"required": True, "max_length": 10, "label": "回收地點行政區"},
    "pickup.address": {"required": True, "min_length": 1, "max_length": 200, "label": "回收地址"},
    "pickup.has_elevator": {"required": True, "type": "bool", "label": "有無電梯"},
    "pickup.need_certificate": {"required": True, "type": "bool", "label": "需要捐贈證明"},
    "pickup.remark": {"required": False, "max_length": 500, "label": "備註"},

    "other_text": {"required": False, "max_length": 500, "label": "其他輔具說明"},
}

# ---- 送件到中心 ----
# False = 預約只記錄在本機 DB，不送到中心、不追蹤中心狀態；聯絡資料（個資）不保存
FORWARD_TO_CENTER = False

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


# ---- 測試模式：模擬資料變化 ----
# True = 測試模式下每次抓資料，假資料都會有變化（缺貨 → 有貨、出現新公告），讓「抓到變化就推播」真的會發生
TEST_SIMULATE_CHANGES = True
TEST_SIM_ARRIVALS_PER_SYNC: int | None = None  # 每次抓取讓幾個「有人訂閱的缺貨品項」到貨；None = 全部
TEST_SIM_NOTICE_EVERY = 3  # 每抓幾次出現一則新公告


def test_api_enabled() -> bool:
    """測試 API / 測試面板要同時：config 開著 + .env TEST_MODE=true。"""
    return API_ENABLED.get("test", False) and get_settings().test_mode
