from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from decimal import Decimal
from typing import List
from app.movies.schemas import MovieShortResponse


class CartItemAdd(BaseModel):
    movie_id: int = Field(..., gt=0)


class CartItemResponse(BaseModel):
    added_at: datetime
    movie: MovieShortResponse

    model_config = ConfigDict(from_attributes=True)


class CartResponse(BaseModel):
    items: List[CartItemResponse]
    total_count: int
    total_price: Decimal

    model_config = ConfigDict(from_attributes=True)


class PurchaseResponse(BaseModel):
    message: str
    purchased_items_count: int
    total_paid: Decimal