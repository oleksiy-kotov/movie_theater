import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal

from app.auth.models import UserModel, UserGroupModel

from app.movies.models import MovieModel
from app.cart.models import CartModel, CartItemModel
from app.orders.models import OrderModel

async def create_superuser():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(UserGroupModel).where(UserGroupModel.name == "admin"))
        admin_group = result.scalar_one_or_none()

        if not admin_group:
            admin_group = UserGroupModel(name="admin")
            db.add(admin_group)
            await db.flush()

        admin = UserModel.create(
            email="admin@example.com",
            raw_password="Admin@123",
            group_id=admin_group.id
        )
        admin.is_admin = True
        admin.is_active = True

        db.add(admin)
        await db.commit()


if __name__ == "__main__":
    asyncio.run(create_superuser())