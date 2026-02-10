import asyncio

from app.database import AsyncSessionLocal

from sqlalchemy import select
from app.auth.models import *
from app.movies.models import *
from app.cart.models import *
from app.database import Base


async def seed_data():
    async with AsyncSessionLocal() as session:
        groups = ["USER", "MODERATOR", "ADMIN"]

        for name in groups:
            stmt = select(UserGroupModel).where(UserGroupModel.name == name)
            result = await session.execute(stmt)
            existing_group = result.scalar_one_or_none()

            if not existing_group:
                group = UserGroupModel(name=name)
                session.add(group)
                print(f"Adding group: {name}")
            else:
                print(f"Group {name} already exists, skipping...")

        await session.commit()
        print("Done!")


if __name__ == "__main__":
    asyncio.run(seed_data())
