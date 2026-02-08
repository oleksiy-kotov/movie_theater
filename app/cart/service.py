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

    valid_items = []
    for item in cart.items:
        is_bought = await crud.is_movie_bought(db, user_id, item.movie_id)
        if not is_bought:
            valid_items.append(item)
        else:
            await crud.remove_item_from_cart(db, cart.id, item.movie_id)

    total_price = sum(item.movie.price for item in valid_items)

    return {
        "items": valid_items,
        "total_count": len(valid_items),
        "total_price": total_price
    }

async def checkout_cart(db: AsyncSession, user_id: int):
    cart = await crud.get_or_create_cart(db, user_id)
    if not cart.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your cart is empty"
        )

    movie_ids = []
    for item in cart.items:
        if await crud.is_movie_bought(db, user_id, item.movie_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Movie '{item.movie.title}' is already in your collection"
            )
        movie_ids.append(item.movie_id)

    total_paid = sum(item.movie.price for item in cart.items)

    try:
        await crud.add_to_bought(db, user_id, movie_ids)
        await crud.clear_cart(db, cart.id)
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during checkout"
        )

    return {"purchased_items_count": len(movie_ids), "total_paid": total_paid}