from app.modules.auth.schemas import TokenResponse
from app.modules.auth.security import create_access_token
from app.modules.user.service import UserService


class AuthService:
    def __init__(self, user_service: UserService):
        self.user_service = user_service

    def login(
        self,
        email: str,
        password: str,
    ) -> TokenResponse:
        user = self.user_service.authenticate_user(
            email=email,
            password=password,
        )

        access_token = create_access_token(
            user_id=user.id,
            company_id=user.company_id,
        )

        return TokenResponse(
            access_token=access_token,
        )