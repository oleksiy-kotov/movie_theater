from fastapi import status, HTTPException
from sqlalchemy.exc import SQLAlchemyError

from app.database import AsyncSession
from app.auth.models import UserGroupEnum
from app.notifications.interfaces import EmailSenderInterface
from app.auth.schemas import (
    UserRegistrationRequestSchema,
    UserRegistrationResponseSchema,
)
from app.auth import crud
from app.core import security
from app.auth.crud import get_token_with_user
from app.core.interface import JWTAuthManagerInterface
from app.auth.crud import create_refresh_token


async def register_user(
    db: AsyncSession,
    user_data: UserRegistrationRequestSchema,
    email_sender: EmailSenderInterface,
) -> UserRegistrationResponseSchema:
    hashed_password = security.hash_password(user_data.password)
    user_dict = {"email": str(user_data.email), "password": hashed_password}

    user_group = await crud.get_group_by_name(db, UserGroupEnum.USER)
    if not user_group:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Default user group not found.",
        )

    existing_user = await crud.get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A user with this email {user_data.email} already exists.",
        )
    try:
        new_user, token = await crud.create_user(db, user_dict, user_group.id)

        activation_link = f"http://127.0.0.1:8000/accounts/activate/{token.id}"
        await email_sender.send_activation_email(new_user.email, activation_link)
        return new_user
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


async def deactivate_user(db: AsyncSession, user_id: int):
    success = await crud.delete_user(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} was not found.",
        )
    return {"detail": f"User with id {user_id} was successfully deactivated."}


async def activate_user_account(
    db: AsyncSession,
    token_id: int,
):
    token_obj = await get_token_with_user(db, token_id)
    if not token_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired activation link",
        )
    user = token_obj.user
    if user.is_active:
        return {"message": "Account already activated."}
    await crud.activate_user(db, user, token_obj)
    return {"message": "Account has been activated."}


async def login_user(
    db: AsyncSession, email: str, password: str, jwt_manager: JWTAuthManagerInterface
):
    user = await crud.get_user_by_email(db, email)
    if not user or not security.verify_password(password, user._hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Incorrect email or password.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not activated. Please check your email.",
        )
    token_data = {"sub": user.email}
    access_token = jwt_manager.create_access_token(data=token_data)
    refresh_token = jwt_manager.create_refresh_token(data=token_data)

    await create_refresh_token(
        db,
        user_id=user.id,
        token=refresh_token,
        days_valid=5
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }
