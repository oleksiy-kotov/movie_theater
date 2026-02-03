from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status

from app.api.dependencies import get_accounts_email_notificator, get_s3_storage_client
from app.database import get_db
from app.auth.schemas import (
    UserRegistrationResponseSchema,
    UserRegistrationRequestSchema,
    UserLoginResponseSchema,
    PasswordResetRequestSchema,
    PasswordResetCompleteSchema,
    MessageResponseSchema,
    UserLoginRequestSchema,
    ProfileResponseSchema,
    ProfileCreateSchema,
    ResendEmailRequestSchema,
)
from app.auth.dependencies import get_jwt_auth_manager, get_current_user
from app.auth.models import UserModel
from app.auth.schemas import TokenRefreshRequestSchema, TokenRefreshResponseSchema
from app.notifications.interfaces import EmailSenderInterface
from app.auth import service
from storages.interfaces import S3StorageInterface

auth_router = APIRouter(prefix="/accounts", tags=["Accounts"])


@auth_router.post(
    "/register",
    response_model=UserRegistrationResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="User Registration",
    description="Register a new user with an email and password.",
    responses={
        409: {
            "description": "Conflict - User with this email already exists.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "A user with this email test@example.com already exists."
                    }
                }
            },
        },
        500: {
            "description": "Internal Server Error - An error occurred during user creation.",
            "content": {
                "application/json": {
                    "example": {"detail": "An error occurred during user creation."}
                }
            },
        },
    },
)
async def signup(
    user_data: UserRegistrationRequestSchema,
    db: AsyncSession = Depends(get_db),
    email_sender=Depends(get_accounts_email_notificator),
):
    """Endpoint for user registration."""

    return await service.register_user(db, user_data, email_sender)


@auth_router.get(
    "/activate/{token_id}",
    response_model=MessageResponseSchema,
    summary="Activate User Account",
    description="Activate a user's account using their email and activation token.",
    status_code=status.HTTP_200_OK,
    responses={
        400: {
            "description": "Bad Request - The activation token is invalid or expired, "
            "or the user account is already active.",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_token": {
                            "summary": "Invalid Token",
                            "value": {"detail": "Invalid or expired activation token."},
                        },
                        "already_active": {
                            "summary": "Account Already Active",
                            "value": {"detail": "User account is already active."},
                        },
                    }
                }
            },
        },
    },
)
async def activate(
    token_id: int,
    db: AsyncSession = Depends(get_db),
    email_sender=Depends(get_accounts_email_notificator),
):
    """Endpoint to activate a user's account."""
    return await service.activate_user_account(db, token_id, email_sender)


@auth_router.post(
    "/resend-activation",
    response_model=MessageResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Request a new activation email",
)
async def resend_activation(
    email_data: ResendEmailRequestSchema,
    db: AsyncSession = Depends(get_db),
    email_sender: EmailSenderInterface = Depends(get_accounts_email_notificator),
):

    return await service.resend_activation_token(
        db=db,
        email_data=email_data,
        email_sender=email_sender
    )

@auth_router.post(
    "/login",
    response_model=UserLoginResponseSchema,
    summary="User Login",
    description="Authenticate a user and return access and refresh tokens.",
    status_code=status.HTTP_200_OK,
    responses={
        401: {
            "description": "Unauthorized - Invalid email or password.",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid email or password."}
                }
            },
        },
        403: {
            "description": "Forbidden - User account is not activated.",
            "content": {
                "application/json": {
                    "example": {"detail": "User account is not activated."}
                }
            },
        },
        500: {
            "description": "Internal Server Error - An error occurred while processing the request.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "An error occurred while processing the request."
                    }
                }
            },
        },
    },
)
async def login(
    login_data: UserLoginRequestSchema,
    db: AsyncSession = Depends(get_db),
    jwt_manager=Depends(get_jwt_auth_manager),
):
    """Endpoint for user login."""
    return await service.login_user(db, login_data, jwt_manager=jwt_manager)


@auth_router.post(
    "/refresh",
    response_model=TokenRefreshResponseSchema,
    summary="Refresh Access Token",
    description="Refresh the access token using a valid refresh token.",
    status_code=status.HTTP_200_OK,
    responses={
        400: {
            "description": "Bad Request - The provided refresh token is invalid or expired.",
            "content": {
                "application/json": {"example": {"detail": "Token has expired."}}
            },
        },
        401: {
            "description": "Unauthorized - Refresh token not found.",
            "content": {
                "application/json": {"example": {"detail": "Refresh token not found."}}
            },
        },
        404: {
            "description": "Not Found - The user associated with the token does not exist.",
            "content": {"application/json": {"example": {"detail": "User not found."}}},
        },
    },
)
async def refresh_token(
    token_data: TokenRefreshRequestSchema,
    db: AsyncSession = Depends(get_db),
    jwt_manager=Depends(get_jwt_auth_manager),
):
    """Endpoint to refresh an access token."""
    return await service.refresh_user_token(
        db, refresh_token=token_data.refresh_token, jwt_manager=jwt_manager
    )


@auth_router.post(
    "/password-reset/request/",
    response_model=MessageResponseSchema,
    summary="Request Password Reset Token",
    description=(
        "Allows a user to request a password reset token. If the user exists and is active, "
        "a new token will be generated and any existing tokens will be invalidated."
    ),
    status_code=status.HTTP_200_OK,
)
async def request_password_reset_token(
    data: PasswordResetRequestSchema,
    db: AsyncSession = Depends(get_db),
    email_sender: EmailSenderInterface = Depends(get_accounts_email_notificator),
):
    """Endpoint to request a password reset token."""
    return await service.password_reset_request(
        db, data, email_sender=email_sender
    )


@auth_router.post(
    "/password-reset/complete",
    response_model=MessageResponseSchema,
    summary="Reset User Password",
    description="Reset a user's password if a valid token is provided.",
    status_code=status.HTTP_200_OK,
    responses={
        400: {
            "description": (
                "Bad Request - The provided email or token is invalid, "
                "the token has expired, or the user account is not active."
            ),
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_email_or_token": {
                            "summary": "Invalid Email or Token",
                            "value": {"detail": "Invalid email or token."},
                        },
                        "expired_token": {
                            "summary": "Expired Token",
                            "value": {"detail": "Invalid email or token."},
                        },
                    }
                }
            },
        },
        500: {
            "description": "Internal Server Error - An error occurred while resetting the password.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "An error occurred while resetting the password."
                    }
                }
            },
        },
    },
)
async def reset_complete(
    data: PasswordResetCompleteSchema,
    db: AsyncSession = Depends(get_db),
):
    """Endpoint for resetting a user's password."""
    return await service.complete_password_reset(db, data)


@auth_router.post(
    "/logout",
    summary="User Logout",
    description="Logout the current user by invalidating their refresh token.",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {
            "description": "Unauthorized - Token is missing, invalid or expired.",
            "content": {
                "application/json": {"example": {"detail": "Not authenticated"}}
            },
        },
        500: {
            "description": "Internal Server Error - Database connection issues.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "An error occurred while processing the request."
                    }
                }
            },
        },
    },
)
async def logout(
    token_data: TokenRefreshRequestSchema,
    db: AsyncSession = Depends(get_db),
):
    """Endpoint to logout the current user by invalidating their refresh token."""

    return await service.logout_user(db, token_data.refresh_token.strip())


@auth_router.delete(
    "/delete/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user"
)
async def deactivate(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await service.deactivate_user(db, user_id)


@auth_router.post("/{user_id}/profile", response_model=ProfileResponseSchema)
async def create_profile(
        user_id: int,
        current_user: UserModel = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
        s3_client: S3StorageInterface = Depends(get_s3_storage_client),
        profile_data: ProfileCreateSchema = Depends(ProfileCreateSchema.from_form)
):
    profile = await service.setup_profile(db, user_id, current_user, profile_data, s3_client)
    avatar_url = await s3_client.get_file_url(profile.avatar)
    profile_schema = ProfileResponseSchema(
        id=profile.id,
        user_id=profile.user_id,
        first_name=profile.first_name,
        last_name=profile.last_name,
        gender=profile.gender,
        date_of_birth=profile.date_of_birth,
        info=profile.info,
        avatar=avatar_url,
    )

    return profile_schema.model_dump()

@auth_router.get("/me", response_model=ProfileResponseSchema)
async def get_my_profile(current_user: UserModel = Depends(get_current_user)):
    profile = current_user.profile

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found.",
        )

    return ProfileResponseSchema.model_validate(profile)
