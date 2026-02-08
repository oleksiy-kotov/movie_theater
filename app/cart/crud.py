from sqlalchemy import select, delete, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.cart.models import CartModel, CartItemModel, bought_movies_table

async def get_or_create_cart(db: AsyncSession, user_id: int):
    stmt = select(CartModel).where(CartModel.user_id == user_id).options(
        selectinload(CartModel.items).selectinload(CartItemModel.movie)
    )
    result = await db.execute(stmt)
    cart = result.scalar_one_or_none()

    if not cart:
        cart = CartModel(user_id=user_id)
        db.add(cart)
        await db.commit()
        await db.refresh(cart)
    return cart

async def add_item_to_cart(db: AsyncSession, cart_id: int, movie_id: int):
    item = CartItemModel(cart_id=cart_id, movie_id=movie_id)
    db.add(item)
    await db.commit()
    return item

async def is_movie_bought(db: AsyncSession, user_id: int, movie_id: int):
    stmt = select(bought_movies_table).where(
        bought_movies_table.c.user_id == user_id,
        bought_movies_table.c.movie_id == movie_id
    )
    result = await db.execute(stmt)
    return result.first() is not None

async def clear_cart(db: AsyncSession, cart_id: int):
    await db.execute(delete(CartItemModel).where(CartItemModel.cart_id == cart_id))

async def add_to_bought(db: AsyncSession, user_id: int, movie_ids: list[int]):
    if not movie_ids:
        return
    values = [{"user_id": user_id, "movie_id": mid} for mid in movie_ids]
    await db.execute(insert(bought_movies_table).values(values))

async def remove_item_from_cart(db: AsyncSession, cart_id: int, movie_id: int) -> bool:
    stmt = delete(CartItemModel).where(
        CartItemModel.cart_id == cart_id,
        CartItemModel.movie_id == movie_id
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0

async def get_cart_by_user_id(db: AsyncSession, user_id: int):
    stmt = select(CartModel).where(CartModel.user_id == user_id).options(
        selectinload(CartModel.items).selectinload(CartItemModel.movie)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()