"""Firebase Cloud Messaging（HTTP v1）發送工具。iOS 也走 FCM，由 FCM 轉 APNs。

設定（.env）：
    FCM_PROJECT_ID=台北通 App 的 Firebase 專案 ID
    FCM_CREDENTIALS_FILE=服務帳號金鑰 JSON 路徑（不要 commit 進 repo）
沒設定時 is_enabled() 為 False，推播直接略過，事件仍然寫進信箱（App 打開時可補拉）。

⚠ 通知會出現在鎖定畫面：title / body 不可放姓名、身分證、電話、輔具名稱。
"""

import asyncio
from enum import Enum

from app.config import get_settings
from app.tools.http_client import get_http_client
from app.tools.logger import get_logger

logger = get_logger(__name__)

SCOPE = "https://www.googleapis.com/auth/firebase.messaging"


class SendResult(str, Enum):
    OK = "ok"
    INVALID_TOKEN = "invalid_token"  # token 失效 → 呼叫端要刪掉這個裝置
    RETRY = "retry"  # 暫時失敗（429、5xx、網路）→ 之後重試
    FAILED = "failed"  # 其他錯誤，不重試
    LOCAL = "local"  # 只記錄在本機，沒送到手機（沒設定 FCM，或是本機假裝置 local-*）


_credentials = None
_lock = asyncio.Lock()


def is_enabled() -> bool:
    s = get_settings()
    return bool(s.fcm_project_id and s.fcm_credentials_file)


async def _access_token() -> str:
    """服務帳號換 OAuth token；過期才重新換（google-auth 是同步的，丟到 thread）。"""
    global _credentials
    async with _lock:
        if _credentials is None:
            from google.oauth2 import service_account

            _credentials = service_account.Credentials.from_service_account_file(
                get_settings().fcm_credentials_file, scopes=[SCOPE]
            )
        if not _credentials.valid:
            from google.auth.transport.requests import Request

            await asyncio.to_thread(_credentials.refresh, Request())
        return _credentials.token


def build_message(*, title: str, body: str, data: dict[str, str],
                  token: str | None = None, topic: str | None = None) -> dict:
    target = {"token": token} if token else {"topic": topic}
    return {
        "message": {
            **target,
            "notification": {"title": title, "body": body},
            "data": {k: str(v) for k, v in data.items() if v is not None},  # FCM data 只收字串
            "android": {"priority": "high", "notification": {"channel_id": "assistive"}},
            "apns": {"headers": {"apns-priority": "10"}, "payload": {"aps": {"sound": "default"}}},
        }
    }


LOCAL_TOKEN_PREFIX = "local-"  # 測試用本機假裝置，不送 FCM


def local_token(mailbox_id: str) -> str:
    return f"{LOCAL_TOKEN_PREFIX}{mailbox_id}"


async def send(message: dict) -> SendResult:
    if not is_enabled() or message["message"].get("token", "").startswith(LOCAL_TOKEN_PREFIX):
        return SendResult.LOCAL
    url = f"https://fcm.googleapis.com/v1/projects/{get_settings().fcm_project_id}/messages:send"
    try:
        token = await _access_token()
        res = await get_http_client().post(url, json=message, headers={"Authorization": f"Bearer {token}"},
                                           timeout=10.0)
    except Exception as exc:  # noqa: BLE001  網路錯誤 → 重試
        logger.warning("FCM send error: %s", type(exc).__name__)
        return SendResult.RETRY

    if res.status_code == 200:
        return SendResult.OK
    status = ""
    try:
        status = res.json().get("error", {}).get("status", "")
    except ValueError:
        pass
    # 不記錄 token 與通知內容
    if res.status_code == 404 or status in ("UNREGISTERED", "NOT_FOUND"):
        return SendResult.INVALID_TOKEN
    if res.status_code == 400 and status == "INVALID_ARGUMENT" and "token" in message["message"]:
        return SendResult.INVALID_TOKEN
    if res.status_code == 429 or res.status_code >= 500:
        return SendResult.RETRY
    logger.warning("FCM send failed: %s %s", res.status_code, status)
    return SendResult.FAILED
