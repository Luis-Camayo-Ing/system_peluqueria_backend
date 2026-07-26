from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.schemas import TokenResponse
from app.modules.auth.service import AuthService
from app.modules.user.repository import UserRepository
from app.modules.user.service import UserService


router = APIRouter(
    prefix="/auth",
    tags=["Autenticación"],
)


def get_auth_service(
    db: Session = Depends(get_db),
) -> AuthService:
    user_repository = UserRepository(db)
    user_service = UserService(user_repository)

    return AuthService(user_service)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    return service.login(
        email=form_data.username,
        password=form_data.password,
    )