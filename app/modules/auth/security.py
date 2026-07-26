from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from jwt import InvalidTokenError

from app.core.config import settings


def create_access_token(
    user_id: UUID,
    company_id: UUID,
) -> str:
    now = datetime.now(UTC)

    payload = {
        "sub": str(user_id),
        "company_id": str(company_id),
        "iat": now,
        "exp": now
        + timedelta(
            minutes=settings.access_token_expire_minutes
        ),
    }

    return jwt.encode(
        payload,
        settings.secret_key,
        algorithm=settings.algorithm,
    )


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
    except InvalidTokenError as error:
        raise ValueError("Token inválido o expirado") from error