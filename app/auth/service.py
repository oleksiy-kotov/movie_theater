from datetime import timezone, datetime

from fastapi import status, HTTPException
from sqlalchemy.exc import SQLAlchemyError


from app.database import AsyncSession
from app.auth.models import UserGroupEnum, UserModel, UserProfileModel
from app.notifications.interfaces import EmailSenderInterface
from app.auth.schemas import (
    UserRegistrationRequestSchema,
    UserRegistrationResponseSchema,
    UserLoginResponseSchema,
    MessageResponseSchema,
    PasswordResetRequestSchema,
    PasswordResetCompleteSchema,
    ResendEmailRequestSchema,
)
from app.auth import crud
from app.core import security
from app.core.interface import JWTAuthManagerInterface
from app.auth.schemas import UserLoginRequestSchema
from app.auth.schemas import TokenRefreshResponseSchema
from app.auth.schemas import ProfileCreateSchema
from app.exceptions import S3FileUploadError
from storages.interfaces import S3StorageInterface

BASE_URL = "http://127.0.0.1:8000"


async def register_user(
    db: AsyncSession,
    user_data: UserRegistrationRequestSchema,
    email_sender: EmailSenderInterface,
) -> UserRegistrationResponseSchema:

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
        new_user, token = await crud.create_user(
            db,
            email=user_data.email,
            password=user_data.password,
            group_id=user_group.id,
        )
        await db.commit()
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during user creation.",
        ) from e
    else:
        activation_link = f"{BASE_URL}/accounts/activate/{token.id}"
        await email_sender.send_activation_email(new_user.email, activation_link)
    return UserRegistrationResponseSchema.model_validate(new_user)


async def activate_user_account(
    db: AsyncSession,
    token_id: int,
    email_sender: EmailSenderInterface,
):
    token_obj = await crud.get_token_with_user(db, token_id)
    if not token_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired activation link",
        )
    if hasattr(token_obj, "expires_at"):
        now = datetime.now(timezone.utc)
        if token_obj.expires_at.replace(tzinfo=timezone.utc) < now:
            await db.delete(token_obj)
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Activation link has expired.",
            )
    user = token_obj.user
    if user.is_active:
        await db.delete(token_obj)
        await db.commit()
        return MessageResponseSchema(message="Account already activated.")
    try:
        await crud.activate_user(db, user, token_obj)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Error during activation") from e

    login_link = f"{BASE_URL}/accounts/login/"
    await email_sender.send_activation_complete_email(user.email, login_link)

    return MessageResponseSchema(
        message="Account activated and confirmation email sent!"
    )

async def resend_activation_token(
    db: AsyncSession,
    email_data: ResendEmailRequestSchema,
    email_sender: EmailSenderInterface,
) -> MessageResponseSchema:

    user = await crud.get_user_by_email(db, email_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email not found.",
        )

    if user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account already activated.",
        )

    try:
        await crud.delete_old_activation_tokens(db, user_id=user.id)
        new_token = await crud.create_activation_token(db, user_id=user.id)

        activation_link = f"{BASE_URL}/accounts/activate/{new_token.secret}"
        await email_sender.send_activation_email(user.email, activation_link)

        await db.commit()

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not resend activation email.",
        ) from e

    return MessageResponseSchema(message="New activation link sent to your email.")


async def login_user(
    db: AsyncSession,
    login_data: UserLoginRequestSchema,
    jwt_manager: JWTAuthManagerInterface,
) -> UserLoginResponseSchema:
    user = await crud.get_user_by_email(db, login_data.email)

    if not user or not security.verify_password(
        login_data.password, user._hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Incorrect email or password.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not activated. Please check your email.",
        )

    jwt_refresh_token = jwt_manager.create_refresh_token({"sub": str(user.id)})

    try:
        await crud.create_refresh_token(
            db, user_id=user.id, token=jwt_refresh_token, days_valid=5
        )
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating session.",
        ) from e
    jwt_access_token = jwt_manager.create_access_token({"sub": str(user.id)})

    return UserLoginResponseSchema(
        access_token=jwt_access_token,
        refresh_token=jwt_refresh_token,
        token_type="bearer",
    )


async def refresh_user_token(
    db: AsyncSession,
    refresh_token: str,
    jwt_manager: JWTAuthManagerInterface,
):
    try:
        decode_token = jwt_manager.decode_refresh_token(refresh_token)
        user_id = decode_token.get("sub")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    db_token = await crud.get_refresh_token(db, token=refresh_token)
    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token not found in database",
        )
    try:
        await crud.delete_refresh_token(db, token=refresh_token)

        new_access_token = jwt_manager.create_access_token(data={"sub": user_id})
        new_refresh_token = jwt_manager.create_refresh_token(data={"sub": user_id})

        await crud.create_refresh_token(
            db, user_id=db_token.user_id, token=new_refresh_token, days_valid=5
        )
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating session.",
        ) from e
    return TokenRefreshResponseSchema(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
    )


async def logout_user(db: AsyncSession, refresh_token: str):
    result = await crud.delete_refresh_token(db, token=refresh_token)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token not found in database",
        )
    return MessageResponseSchema(message="Logged out successfully")


async def password_reset_request(
    db: AsyncSession,
    data: PasswordResetRequestSchema,
    email_sender: EmailSenderInterface,
):
    user = await crud.get_user_by_email(db, data.email)
    if user and user.is_active:
        reset_token = await crud.create_password_reset_token(db, user.id)
        reset_link = f"{BASE_URL}/accounts/password-reset-complete/{reset_token.token}"
        await email_sender.send_password_reset_email(user.email, reset_link)
    return MessageResponseSchema(
        message="If the email is registered, instructions have been sent."
    )


async def complete_password_reset(
    db: AsyncSession,
    data: PasswordResetCompleteSchema,
):
    token_obj = await crud.get_password_reset_token(db, data.token)
    if not token_obj:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset link",
        )
    user = token_obj.user
    user._hashed_password = security.hash_password(data.password)
    await db.delete(token_obj)
    await crud.revoke_all_user_sessions(db, user.id)

    await db.commit()

    return MessageResponseSchema(message="Password reset has been completed.")


async def deactivate_user(db: AsyncSession, user_id: int):
    success = await crud.delete_user(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} was not found.",
        )


async def setup_profile(
    db: AsyncSession,
    user_id: int,
    current_user: UserModel,
    profile_data: ProfileCreateSchema,
    s3_client: S3StorageInterface,
):

    if current_user.id != user_id and current_user.group.name == UserGroupEnum.USER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied."
        )
    if await crud.get_profile_user_by_id(db, user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with id {user_id} already exists.",
        )
    avatar_bytes = await profile_data.avatar.read()
    avatar_key = f"avatars/{user_id}_{profile_data.avatar.filename}"

    try:
        await s3_client.upload_file(file_name=avatar_key, file_data=avatar_bytes)
    except S3FileUploadError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="S3 upload failed.",
        )
    new_profile = UserProfileModel(
        user_id=user_id,
        first_name=profile_data.first_name,
        last_name=profile_data.last_name,
        gender=profile_data.gender,
        date_of_birth=profile_data.date_of_birth,
        info=profile_data.info,
        avatar=avatar_key,
    )
    return await crud.create_user_profile(db, new_profile)
