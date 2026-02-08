from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.orders import service, schemas, crud
from app.auth.dependencies import get_current_user
from app.database import get_db

order_router = APIRouter(prefix="/orders", tags=["Orders"])

@order_router.get("/", response_model=list[schemas.OrderResponse])
async def get_my_orders(
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user)
):
    return await crud.get_user_orders(db, user.id)

@order_router.post("/create", response_model=schemas.OrderResponse)
async def create_new_order(
        db: AsyncSession = Depends(get_db),
        user=Depends(get_current_user)
):
    return await service.initiate_checkout(db, user.id)


@order_router.post("/{order_id}/pay")
async def pay_for_order(
        order_id: int,
        db: AsyncSession = Depends(get_db),
        user=Depends(get_current_user)
):
    return await service.complete_order(db, order_id, user.id)


@order_router.post("/{order_id}/cancel")
async def cancel_my_order(
        order_id: int,
        db: AsyncSession = Depends(get_db),
        user=Depends(get_current_user)
):
    return await service.cancel_order(db, order_id, user.id)


@order_router.get("/{order_id}", response_model=schemas.OrderResponse)
async def get_order_details(
        order_id: int,
        db: AsyncSession = Depends(get_db),
        user=Depends(get_current_user)
):
    order = await crud.get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return order