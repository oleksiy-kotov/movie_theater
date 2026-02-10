from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, insert
from sqlalchemy.orm import selectinload
from app.orders.models import OrderModel, OrderItemModel, OrderStatus
from decimal import Decimal

from app.cart.models import bought_movies_table


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

    await db.commit()

    result = await db.execute(
        select(OrderModel)
        .options(
            selectinload(OrderModel.items).selectinload(OrderItemModel.movie)
        )
        .where(OrderModel.id == new_order.id)
    )
    return result.scalar_one()

async def add_movies_to_user_library(db: AsyncSession, user_id: int, movie_ids: list[int]):
    if not movie_ids:
        return
    data = [{"user_id": user_id, "movie_id": m_id} for m_id in movie_ids]
    stmt = insert(bought_movies_table).values(data)

    await db.execute(stmt)

async def update_order_status(db: AsyncSession, order_id: int, status: OrderStatus):
    await db.execute(
        update(OrderModel)
        .where(OrderModel.id == order_id)
        .values(status=status)
    )
    await db.flush()

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