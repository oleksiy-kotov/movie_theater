from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from app.orders.models import OrderModel, OrderItemModel, OrderStatus
from decimal import Decimal


async def get_order_by_id(db: AsyncSession, order_id: int) -> OrderModel:
    result = await db.execute(
        select(OrderModel)
        .where(OrderModel.id == order_id)
        .options(selectinload(OrderModel.items))
    )
    return result.scalar_one_or_none()


async def create_order(db: AsyncSession, user_id: int, total_amount: Decimal, items_data: list):
    new_order = OrderModel(
        user_id=user_id,
        total_amount=total_amount,
        status=OrderStatus.pending
    )
    db.add(new_order)
    await db.flush()

    for item in items_data:
        order_item = OrderItemModel(
            order_id=new_order.id,
            movie_id=item["movie_id"],
            price_at_order=item["price"]
        )
        db.add(order_item)

    return new_order


async def update_order_status(db: AsyncSession, order_id: int, status: OrderStatus):
    query = update(OrderModel).where(OrderModel.id == order_id).values(status=status)
    await db.execute(query)


async def get_pending_order(db: AsyncSession, user_id: int):
    query = (
        select(OrderModel)
        .where(OrderModel.user_id == user_id, OrderModel.status == OrderStatus.pending)
        .options(selectinload(OrderModel.items))
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_user_orders(db: AsyncSession, user_id: int):
    query = (
        select(OrderModel)
        .where(OrderModel.user_id == user_id)
        .order_by(OrderModel.created_at.desc())
        .options(selectinload(OrderModel.items))
    )
    result = await db.execute(query)
    return result.scalars().all()