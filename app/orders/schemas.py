from pydantic import BaseModel
from datetime import datetime
from typing import List
from decimal import Decimal
from app.orders.models import OrderStatus

class OrderItemSchema(BaseModel):
    movie_id: int
    price_at_order: Decimal

    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    id: int
    status: OrderStatus
    total_amount: Decimal
    created_at: datetime
    items: List[OrderItemSchema]

    class Config:
        from_attributes = True