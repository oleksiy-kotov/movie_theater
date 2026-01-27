from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status

from app.api.dependencies import get_accounts_email_notificator
from app.database import get_db
from app.auth.schemas import (
    UserRegistrationResponseSchema,
    UserRegistrationRequestSchema,
    UserLoginResponseSchema,
)
from app.auth.service import register_user, deactivate_user, login_user
from app.auth.service import activate_user_account
from app.auth.dependencies import get_jwt_auth_manager, get_current_user
from app.auth.models import UserModel
from app.auth.crud import get_refresh_token, delete_refresh_token

auth_router = APIRouter(prefix="/accounts", tags=["Accounts"])


@auth_router.post(
    "/register",
    response_model=UserRegistrationResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def signup(
    user_data: UserRegistrationRequestSchema,
    db: AsyncSession = Depends(get_db),
    email_sender=Depends(get_accounts_email_notificator),
):
    return await register_user(db, user_data, email_sender)


@auth_router.delete(
    "/delete/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a user"
)
async def deactivate(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await deactivate_user(db, user_id)


@auth_router.get("/activate/{token_id}")
async def activate(token_id: int, db: AsyncSession = Depends(get_db)):
    return await activate_user_account(db, token_id)


@auth_router.post("/login", response_model=UserLoginResponseSchema)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    jwt_manager=Depends(get_jwt_auth_manager),
):
    result = await login_user(db, form_data.username, form_data.password, jwt_manager)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    return result


@auth_router.get("/me")
async def get_my_profile(current_user: UserModel = Depends(get_current_user)):
    return {
        "email": current_user.email,
        "status": "Activate" if current_user.is_active else "Pending",
        "registered_on": current_user.created_at,
    }


@auth_router.post("/logout")
async def logout(
    refresh_token: str,
    db: AsyncSession = Depends(get_db),
):
    db_token = await get_refresh_token(db, token=refresh_token)
    if not db_token:
        raise HTTPException(status_code=404, detail="Token not found")

    await delete_refresh_token(db, token=refresh_token)

    return {"message": "Logged out successfully"}
