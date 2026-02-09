from typing import Optional

from pydantic import BaseModel, ConfigDict
from decimal import Decimal
from datetime import datetime
from app.payments.models import PaymentStatus

class PaymentResponse(BaseModel):
    id: int
    order_id: int
    status: PaymentStatus
    amount: Decimal
    external_payment_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class StripeSessionResponse(BaseModel):
    checkout_url: str
    payment_intent_id: Optional[str]