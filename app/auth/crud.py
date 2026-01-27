from sqlalchemy import select, delete
from sqlalchemy.orm import joinedload

from app.auth.models import UserModel, UserGroupModel, UserGroupEnum
from app.database import AsyncSession
from app.auth.models import ActivationTokenModel
from app.auth.models import RefreshTokenModel


async def get_group_by_name(db: AsyncSession, name: UserGroupEnum):
    result = await db.execute(select(UserGroupModel).where(UserGroupModel.name == name))
    return result.scalars().first()


async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(UserModel).where(UserModel.email == email))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user_in: dict, group_id: int):
    user_data = {**user_in, "group_id": group_id}
    new_user = UserModel(**user_data)
    db.add(new_user)
    await db.flush()

    activation_token = ActivationTokenModel(user_id=new_user.id)
    db.add(activation_token)
    await db.commit()
    await db.refresh(new_user)
    await db.refresh(activation_token)
    return new_user, activation_token


async def delete_user(db: AsyncSession, user_id: int):
    stmt = delete(UserModel).where(UserModel.id == user_id)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0


async def get_token_with_user(db: AsyncSession, token_id: int):
    stmt = (
        select(ActivationTokenModel)
        .where(ActivationTokenModel.id == token_id)
        .options(joinedload(ActivationTokenModel.user))
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def activate_user(db: AsyncSession, user: UserModel, token: ActivationTokenModel):
    user.is_active = True
    await db.delete(token)
    await db.commit()

async def create_refresh_token(db: AsyncSession, user_id: int, token: str, days_valid: int = 5):
    db_token = RefreshTokenModel.create(
        user_id=user_id,
        token=token,
        days_valid=days_valid,
    )
    db.add(db_token)
    await db.commit()
    await db.refresh(db_token)
    return db_token

async def get_refresh_token(db: AsyncSession, token: str):
    result = await db.execute(select(RefreshTokenModel).where(RefreshTokenModel.token == token))
    return result.scalar_one_or_none()

async def delete_refresh_token(db: AsyncSession, token: str):
    await db.execute(delete(RefreshTokenModel).where(RefreshTokenModel.token == token))
    await db.commit()
