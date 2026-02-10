import stripe
from fastapi import HTTPException, status
from app.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from app.cart import service as cart_service
from app.orders import crud as order_crud
from app.cart import crud as cart_crud
from app.orders.models import OrderStatus
from app.payments.models import PaymentModel


stripe.api_key = settings.STRIPE_SECRET_KEY


async def initiate_checkout(db: AsyncSession, user_id: int, user_email: str):
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
    await cart_crud.clear_cart(db, user_id)
    await db.commit()

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f'Order #{order.id}',
                        'description': f'Purchase of {len(items_to_order)} movies',
                    },
                    'unit_amount': int(order.total_amount * 100),
                },
                'quantity': 1,
            }],
            mode='payment',

            success_url=f"{settings.FRONTEND_URL}/payment/success?order_id={order.id}",
            cancel_url=f"{settings.FRONTEND_URL}/payment/cancel?order_id={order.id}",
            customer_email=user_email,
            metadata={"order_id": str(order.id)}
        )

        return {
            "order_id": order.id,
            "checkout_url": checkout_session.url
        }

    except Exception as e:
        await order_crud.update_order_status(db, order.id, "canceled")
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")


async def get_cart_details(db: AsyncSession, user_id: int):
    cart = await cart_crud.get_or_create_cart(db, user_id)
    bought_ids = await cart_crud.get_bought_movie_ids(db, user_id)
    pending_order = await order_crud.get_pending_order(db, user_id)

    valid_items = []
    for item in cart.items:
        if item.movie_id in bought_ids:
            await cart_crud.remove_item_from_cart(db, cart.id, item.movie_id)
        else:
            valid_items.append(item)

    total_price = sum(item.movie.price for item in valid_items)

    return {
        "items": valid_items,
        "total_count": len(valid_items),
        "total_price": total_price,
        "pending_order_id": pending_order.id if pending_order else None
    }


async def complete_order(db: AsyncSession, order_id: int, stripe_id: str):
    try:
        order = await order_crud.get_order_by_id(db, order_id)
        if not order or order.status == "paid":
            return

        order.status = "paid"

        new_payment = PaymentModel(
            order_id=order_id,
            user_id=order.user_id,
            amount=order.total_amount,
            status="successful",
            external_payment_id=stripe_id
        )
        db.add(new_payment)

        movie_ids = [item.movie_id for item in order.items]
        await order_crud.add_movies_to_user_library(db, order.user_id, movie_ids)

        await db.commit()

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Critical error during payment finalization"
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