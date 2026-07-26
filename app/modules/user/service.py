from uuid import UUID

from app.modules.user.exceptions import (
    InactiveUserError,
    InvalidCredentialsError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.modules.user.model import User
from app.modules.user.repository import UserRepository
from app.modules.user.schemas import UserCreate, UserUpdate
from app.modules.user.security import hash_password, verify_password


class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def create_user(self, data: UserCreate) -> User:
        existing_user = self.repository.get_by_email(str(data.email))

        if existing_user:
            raise UserAlreadyExistsError()

        user = User(
            company_id=data.company_id,
            email=str(data.email).lower(),
            hashed_password=hash_password(data.password),
        )

        return self.repository.create(user)

    def get_user(self, user_id: UUID) -> User:
        user = self.repository.get_by_id(user_id)

        if not user:
            raise UserNotFoundError()

        return user

    def get_users(self) -> list[User]:
        return self.repository.get_all()

    def update_user(
        self,
        user_id: UUID,
        data: UserUpdate,
    ) -> User:
        user = self.get_user(user_id)

        update_data = data.model_dump(exclude_unset=True)

        if "email" in update_data:
            new_email = str(update_data["email"]).lower()
            existing_user = self.repository.get_by_email(new_email)

            if existing_user and existing_user.id != user.id:
                raise UserAlreadyExistsError()

            user.email = new_email

        if "password" in update_data:
            user.hashed_password = hash_password(
                update_data["password"]
            )

        if "is_active" in update_data:
            user.is_active = update_data["is_active"]

        if "is_verified" in update_data:
            user.is_verified = update_data["is_verified"]

        return self.repository.update(user)

    def delete_user(self, user_id: UUID) -> None:
        user = self.get_user(user_id)
        self.repository.delete(user)

    def authenticate_user(
        self,
        email: str,
        password: str,
    ) -> User:
        user = self.repository.get_by_email(email.lower())

        if not user:
            raise InvalidCredentialsError()

        if not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError()

        if not user.is_active:
            raise InactiveUserError()

        return user