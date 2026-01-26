from fastapi import Depends, status, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.api.dependencies import get_accounts_email_notificator
from app.database import AsyncSession
from app.models.user import UserModel, UserGroupModel, UserGroupEnum, ActivationTokenModel
from app.notifications.interfaces import EmailSenderInterface
from app.schemas.user import (
    UserRegistrationRequestSchema,
    UserRegistrationResponseSchema,
)


async def register_user(
    db: AsyncSession,
    user_data: UserRegistrationRequestSchema,
    email_sender: EmailSenderInterface,
) -> UserRegistrationResponseSchema:
    result = await db.execute(select(UserModel).where(UserModel.email == user_data.email))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A user with this email {user_data.email} already exists.",
        )
    group_result = await db.execute(select(UserGroupModel).where(UserGroupModel.name == UserGroupEnum.USER))
    user_group = group_result.scalars().first()
    if not user_group:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Default user group not found."
        )
    try:
        new_user = UserModel.create(
            email=str(user_data.email),
            raw_password=user_data.password,
            group_id=user_group.id,
        )
        db.add(new_user)
        await db.flush()

        activation_token = ActivationTokenModel(user_id=new_user.id)
        db.add(activation_token)
        await db.commit()
        await db.refresh(new_user)
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during user creation."
        ) from e
    else:
        activation_link = "http://127.0.0.1/accounts/activate/"

        await email_sender.send_activation_email(
            new_user.email,
            activation_link,
        )

        return UserRegistrationResponseSchema.model_validate(new_user)
