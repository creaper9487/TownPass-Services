"""密鑰與簽章工具。

- 密鑰一律 256 位元隨機值，資料庫只存 hash。
- webhook 與推播用 HMAC-SHA256：簽章內容為 f"{timestamp}.{body}"。
"""

import hashlib
import hmac
import secrets
import time


def new_id(prefix: str) -> str:
    """不透明 ID，例如 new_id("mb") -> "mb_3fK9..."。"""
    return f"{prefix}_{secrets.token_urlsafe(9)}"


def new_secret() -> str:
    """256 位元隨機密鑰（mailbox_key、access_key）。"""
    return secrets.token_urlsafe(32)


def hash_secret(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def verify_secret(value: str, hashed: str) -> bool:
    return hmac.compare_digest(hash_secret(value), hashed)


def sign(secret: str, timestamp: str, body: bytes) -> str:
    msg = timestamp.encode() + b"." + body
    return hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()


def verify_signature(
    secret: str, timestamp: str, body: bytes, signature: str, max_skew: int
) -> bool:
    try:
        ts = int(timestamp)
    except (TypeError, ValueError):
        return False
    if abs(time.time() - ts) > max_skew:
        return False
    return hmac.compare_digest(sign(secret, timestamp, body), signature or "")
