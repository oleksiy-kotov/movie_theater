from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.auth.dependencies import get_current_user, get_current_admin
from app.cart import service, schemas, crud

cart_router = APIRouter(prefix="/cart", tags=["User | Cart"])

@cart_router.get("/", response_model=schemas.CartResponse)
async def get_my_cart(
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user)
):
    """Retrieve the current user's cart with total price calculation."""
    return await service.get_cart_details(db, user.id)

@cart_router.post(
    "/items",
    status_code=status.HTTP_201_CREATED
)
async def add_movie(
    item: schemas.CartItemAdd,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user)
):
    """Add a movie to the cart. Validates ownership and duplicates."""
    await service.add_to_cart(db, user.id, item.movie_id)
    return {"message": "Movie added to cart"}

@cart_router.delete("/items/{movie_id}")
async def remove_item(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user)
):
    """Remove a specific movie from the current user's cart."""
    cart = await crud.get_or_create_cart(db, user.id)
    success = await crud.remove_item_from_cart(db, cart.id, movie_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found in cart"
        )
    return {"message": "Movie removed from cart"}

@cart_router.delete("/clear")
async def clear_my_cart(
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user)
):
    """Completely empty the user's cart."""
    cart = await crud.get_or_create_cart(db, user.id)
    await crud.clear_cart(db, cart.id)
    await db.commit()
    return {"message": "Cart cleared successfully"}


@cart_router.get(
    "/admin/{user_id}",
    dependencies=[Depends(get_current_admin)]
)
async def admin_get_user_cart(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Admin only: View any user's cart content."""
    cart = await crud.get_cart_by_user_id(db, user_id)
    if not cart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart is empty or user does not exist"
        )
    return cart