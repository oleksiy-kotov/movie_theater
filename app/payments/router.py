from fastapi import APIRouter, Request, Header, Depends, HTTPException
import stripe
from app.config import settings
from app.orders import service as order_service
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

payment_router = APIRouter(prefix="/payments", tags=["Payments"])


@payment_router.post("/webhook")
async def stripe_webhook(
        request: Request,
        stripe_signature: str = Header(None),
        db: AsyncSession = Depends(get_db)
):
    payload = await request.body()

    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail="Webhook error")

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        order_id = session.get("metadata", {}).get("order_id")
        payment_intent = session.get("payment_intent")

        if order_id:
            await order_service.complete_order(db, int(order_id), payment_intent)

    return {"status": "success"}