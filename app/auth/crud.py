from datetime import datetime, timezone
from sqlalchemy import select, delete
from sqlalchemy.orm import joinedload, selectinload

from app.auth.models import (
    UserModel,
    UserGroupModel,
    UserGroupEnum,
    PasswordResetTokenModel,
    UserProfileModel,
)
from app.database import AsyncSession
from app.auth.models import ActivationTokenModel
from app.auth.models import RefreshTokenModel

async def get_group_by_name(db: AsyncSession, name: UserGroupEnum):
    result = await db.execute(select(UserGroupModel).where(UserGroupModel.name == name))
    return result.scalars().first()

async def get_user_by_id(db: AsyncSession, user_id: int):
    stmt = (
        select(UserModel)
        .options(selectinload(UserModel.group), selectinload(UserModel.profile))
        .where(UserModel.id == user_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(UserModel).where(UserModel.email == email))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, email: str, password: str, group_id: int):
    new_user = UserModel.create(email=email, raw_password=password, group_id=group_id)
    db.add(new_user)

    await db.flush()

    token = await create_activation_token(db, user_id=new_user.id)

    await db.flush()

    await db.refresh(new_user)
    await db.refresh(token)

    return new_user, token

async def get_token_with_user(db: AsyncSession, token_id: int):
    stmt = (
        select(ActivationTokenModel)
        .where(ActivationTokenModel.id == token_id)
        .options(joinedload(ActivationTokenModel.user))
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def create_activation_token(db: AsyncSession, user_id: int):
    new_token = ActivationTokenModel(user_id=user_id)
    db.add(new_token)
    await db.flush()
    return new_token

async def delete_old_activation_tokens(db: AsyncSession, user_id: int):
    stmt = delete(ActivationTokenModel).where(ActivationTokenModel.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def activate_user(db: AsyncSession, user: UserModel, token: ActivationTokenModel):
    user.is_active = True
    await db.delete(token)
    await db.commit()

    await db.refresh(user)


async def create_refresh_token(
    db: AsyncSession, user_id: int, token: str, days_valid: int = 5
):
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
    result = await db.execute(
        select(RefreshTokenModel).where(
            RefreshTokenModel.token == token,
            RefreshTokenModel.expires_at > datetime.now(timezone.utc),
        )
    )
    return result.scalar_one_or_none()


async def delete_refresh_token(db: AsyncSession, token: str):
    stmt = (
        delete(RefreshTokenModel)
        .where(RefreshTokenModel.token == token)
        .returning(RefreshTokenModel.id)
    )
    result = await db.execute(stmt)
    deleted_id = result.scalar_one_or_none()
    await db.commit()
    return deleted_id


async def create_password_reset_token(db: AsyncSession, user_id: int):
    await db.execute(
        delete(PasswordResetTokenModel).where(
            PasswordResetTokenModel.user_id == user_id
        )
    )
    reset_token = PasswordResetTokenModel(user_id=user_id)
    db.add(reset_token)
    await db.commit()
    await db.refresh(reset_token)
    return reset_token


async def get_password_reset_token(db: AsyncSession, token: str):
    stmt = (
        select(PasswordResetTokenModel)
        .where(
            PasswordResetTokenModel.token == token,
            PasswordResetTokenModel.expires_at > datetime.now(timezone.utc),
        )
        .options(joinedload(PasswordResetTokenModel.user))
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def revoke_all_user_sessions(db: AsyncSession, user_id: int):
    await db.execute(
        delete(RefreshTokenModel).where(RefreshTokenModel.user_id == user_id)
    )
    await db.commit()


async def get_profile_user_by_id(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(UserProfileModel).where(UserProfileModel.id == user_id)
    )
    return result.scalar_one_or_none()


async def create_user_profile(db: AsyncSession, profile_obj: UserProfileModel):
    db.add(profile_obj)
    await db.commit()
    await db.refresh(profile_obj)
    return profile_obj

async def delete_user(db: AsyncSession, user_id: int):
    stmt = delete(UserModel).where(UserModel.id == user_id)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0
