"""把 config.FIELDS 的欄位規則轉成 Pydantic 欄位，讓 schemas 直接繼承設定、不寫死。

用法（在 BaseModel 裡）：
    name: field_type("contact.name") = field("contact.name")

規則改 app/config.py 的 FIELDS 就好。
"""

from typing import Any, Literal, Optional

from pydantic import Field

from app import config


def rule(name: str) -> dict:
    return config.FIELDS[name]


def field_type(name: str) -> Any:
    r = rule(name)
    t: Any = bool if r.get("type") == "bool" else str
    if r.get("choices"):
        t = Literal[tuple(r["choices"])]
    return t if r.get("required") else Optional[t]


def field(name: str) -> Any:
    r = rule(name)
    kwargs = {k: r[k] for k in ("min_length", "max_length", "pattern") if k in r}
    return Field(... if r.get("required") else None, description=r.get("label"), **kwargs)


def required_fields(service: str) -> list[str]:
    """這個服務必填的欄位（給 GET /forms/{service}）。"""
    groups = config.SERVICES[service]["groups"]
    base = ["items"] + (["center_id"] if service == "borrow" else [])
    return base + [n for n, r in config.FIELDS.items() if r.get("required") and n.split(".")[0] in groups]
