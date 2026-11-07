from typing import Literal

from pydantic import BaseModel, Field


class DeviceRegister(BaseModel):
    mailbox_id: str
    platform: Literal["fcm"] = "fcm"  # iOS 也走 FCM
    token: str = Field(..., min_length=10, max_length=4096)


class DeviceUnregister(BaseModel):
    token: str = Field(..., min_length=10, max_length=4096)
