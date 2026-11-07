from pydantic import BaseModel


class SubscriptionCreate(BaseModel):
    mailbox_id: str
    variant_id: str


class SubscriptionCreated(BaseModel):
    id: str
