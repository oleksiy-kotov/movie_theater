from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.payments.models import PaymentModel, PaymentItemModel, PaymentStatus
from app.orders.models import OrderModel
from decimal import Decimal


async def create_payment_record(
        db: AsyncSession,
        order: OrderModel,
        external_id: str,
        amount: Decimal
) -> PaymentModel:

    new_payment = PaymentModel(
        user_id=order.user_id,
        order_id=order.id,
        amount=amount,
        external_payment_id=external_id,
        status=PaymentStatus.successful
    )
    db.add(new_payment)
    await db.flush()

    for order_item in order.items:
        payment_item = PaymentItemModel(
            payment_id=new_payment.id,
            order_item_id=order_item.id,
            price_at_payment=order_item.price_at_order
        )
        db.add(payment_item)

    return new_payment


async def get_payment_by_external_id(db: AsyncSession, external_id: str):
    result = await db.execute(
        select(PaymentModel).where(PaymentModel.external_payment_id == external_id)
    )
    return result.scalar_one_or_none()


async def get_user_payments(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(PaymentModel)
        .where(PaymentModel.user_id == user_id)
        .order_by(PaymentModel.created_at.desc())
    )
    return result.scalars().all()