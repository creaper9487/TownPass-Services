from fastapi import APIRouter, Depends, Response

from app.features.mailbox import service as mailbox_service
from app.features.subscription import service
from app.features.subscription.schemas import SubscriptionCreate, SubscriptionCreated
from app.routers.deps import bearer_key

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.post("", status_code=201, response_model=SubscriptionCreated, summary="到貨通知（Bearer mailbox_key）")
async def subscribe(payload: SubscriptionCreate, key: str | None = Depends(bearer_key)):
    mailbox_service.authenticate(payload.mailbox_id, key)
    return SubscriptionCreated(id=await service.create(payload))


@router.delete("/{subscription_id}", status_code=204, summary="取消到貨通知（Bearer mailbox_key）")
async def unsubscribe(subscription_id: str, key: str | None = Depends(bearer_key)):
    sub = service.get(subscription_id)
    mailbox_service.authenticate(sub.mailbox_id, key)
    service.delete(subscription_id)
    return Response(status_code=204)
