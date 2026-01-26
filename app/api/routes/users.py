from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_accounts_email_notificator
from app.database import get_db
from app.schemas.user import UserRegistrationResponseSchema, UserRegistrationRequestSchema
from app.services.user_service import register_user

router = APIRouter()


@router.post("/register", response_model=UserRegistrationResponseSchema)
async def signup(
    user_data: UserRegistrationRequestSchema,
    db: AsyncSession = Depends(get_db),
    email_sender=Depends(get_accounts_email_notificator),
):
    return await register_user(db, user_data, email_sender)
