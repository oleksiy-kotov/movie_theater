from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.api.dependencies import get_settings
from app.config import Settings
from app.core.interface import JWTAuthManagerInterface
from app.core.token_manager import JWTAuthManager
from app.database import AsyncSession, get_db
from app.auth import crud
from app.auth.models import UserModel

security_scheme = HTTPBearer()

def get_jwt_auth_manager(
    settings: Settings = Depends(get_settings),
) -> JWTAuthManagerInterface:
    return JWTAuthManager(
        secret_key_access=settings.SECRET_KEY_ACCESS,
        secret_key_refresh=settings.SECRET_KEY_REFRESH,
        algorithm=settings.JWT_SIGNING_ALGORITHM,
    )

async def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
    jwt_manager: JWTAuthManager = Depends(get_jwt_auth_manager),
) -> UserModel:
    token_str = token.credentials
    payload = jwt_manager.decode_access_token(token_str)
    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials"
        )

    user_id = payload.get("sub")
    user = await  crud.get_user_by_id(db, user_id=int(user_id))
    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="User account is deactivated"
        )
    return user
