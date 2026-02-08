from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.cart import service as cart_service
from app.orders import crud as order_crud
from app.cart import crud as cart_crud
from app.orders.models import OrderStatus


async def initiate_checkout(db: AsyncSession, user_id: int):
    existing_order = await order_crud.get_pending_order(db, user_id)
    if existing_order:
        raise HTTPException(
            status_code=400,
            detail=f"You have an unpaid order (ID: {existing_order.id}). Please pay or cancel it first."
        )

    cart_details = await cart_service.get_cart_details(db, user_id)

    if not cart_details["items"]:
        raise HTTPException(status_code=400, detail="Cart is empty")

    items_to_order = [
        {"movie_id": item.movie_id, "price": item.movie.price}
        for item in cart_details["items"]
    ]

    order = await order_crud.create_order(
        db,
        user_id,
        cart_details["total_price"],
        items_to_order
    )

    await db.commit()
    return order


async def get_cart_details(db: AsyncSession, user_id: int):
    cart = await cart_crud.get_or_create_cart(db, user_id)

    pending_order = await order_crud.get_pending_order(db, user_id)

    valid_items = []
    for item in cart.items:
        is_bought = await cart_crud.is_movie_bought(db, user_id, item.movie_id)
        if not is_bought:
            valid_items.append(item)
        else:
            await cart_crud.remove_item_from_cart(db, cart.id, item.movie_id)

    total_price = sum(item.movie.price for item in valid_items)

    return {
        "items": valid_items,
        "total_count": len(valid_items),
        "total_price": total_price,
        "pending_order_id": pending_order.id if pending_order else None
    }

async def complete_order(db: AsyncSession, order_id: int, user_id: int):
    order = await order_crud.get_order_by_id(db, order_id)

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this order")

    if order.status != OrderStatus.pending:
        raise HTTPException(status_code=400, detail=f"Order cannot be completed. Current status: {order.status}")

    try:
        movie_ids = [item.movie_id for item in order.items]

        await cart_crud.add_to_bought(db, user_id, movie_ids)

        await order_crud.update_order_status(db, order_id, OrderStatus.paid)

        cart = await cart_crud.get_or_create_cart(db, user_id)
        await cart_crud.clear_cart(db, cart.id)

        await db.commit()
        return {"message": "Payment successful. Movies added to your collection.", "order_id": order_id}

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Transaction failed during order completion. Please contact support."
        )


async def cancel_order(db: AsyncSession, order_id: int, user_id: int):
    order = await order_crud.get_order_by_id(db, order_id)

    if not order or order.user_id != user_id:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != OrderStatus.pending:
        raise HTTPException(status_code=400, detail="Only pending orders can be canceled")

    await order_crud.update_order_status(db, order_id, OrderStatus.canceled)
    await db.commit()

    return {"message": "Order canceled successfully"}