from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from app.api.dependencies import get_settings
from app.config import Settings
from app.core.interface import JWTAuthManagerInterface
from app.core.token_manager import JWTAuthManager
from app.auth.crud import get_user_by_email
from app.database import AsyncSession, get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="accounts/login")

def get_jwt_auth_manager(
    settings: Settings = Depends(get_settings),
) -> JWTAuthManagerInterface:
    return JWTAuthManager(
        secret_key_access=settings.SECRET_KEY_ACCESS,
        secret_key_refresh=settings.SECRET_KEY_REFRESH,
        algorithm=settings.JWT_SIGNING_ALGORITHM,
    )

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    jwt_manager: JWTAuthManager = Depends(get_jwt_auth_manager),
):
    payload = jwt_manager.decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

    email = payload.get("sub")
    user = await get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user
