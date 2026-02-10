from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.cart import crud

async def add_to_cart(db: AsyncSession, user_id: int, movie_id: int):
    if await crud.is_movie_bought(db, user_id, movie_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already own this movie"
        )

    cart = await crud.get_or_create_cart(db, user_id)

    for item in cart.items:
        if item.movie_id == movie_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Movie is already in your cart"
            )

    return await crud.add_item_to_cart(db, cart.id, movie_id)

async def get_cart_details(db: AsyncSession, user_id: int):
    cart = await crud.get_or_create_cart(db, user_id)
    bought_ids = await crud.get_bought_movie_ids(db, user_id)
    valid_items = []
    for item in cart.items:
        if item.movie_id not in bought_ids:
            valid_items.append(item)
        else:
            await crud.remove_item_from_cart(db, cart.id, item.movie_id)

    total_price = sum(item.movie.price for item in valid_items)

    return {
        "items": valid_items,
        "total_count": len(valid_items),
        "total_price": total_price
    }

