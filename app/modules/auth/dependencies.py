from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.modules.auth.security import decode_access_token
from app.modules.user.model import User
from app.modules.user.repository import UserRepository
from app.modules.user.service import UserService
from app.db.session import get_db

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No fue posible validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")

        if not user_id:
            raise credentials_exception

        parsed_user_id = UUID(user_id)

    except (ValueError, TypeError):
        raise credentials_exception

    repository = UserRepository(db)
    service = UserService(repository)

    try:
        user = service.get_user(parsed_user_id)
    except Exception:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario está inactivo",
        )

    return user