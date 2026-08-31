from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Sistema de Peluquería"
    app_version: str = "1.0.0"
    environment: Literal["development", "test", "production"] = (
        "development"
    )
    debug: bool = True

    database_url: str

    # JWT
    secret_key: str
    algorithm: Literal["HS256", "HS384", "HS512"] = "HS256"
    access_token_expire_minutes: int = Field(default=30, ge=5, le=1440)

    # HTTP security
    allowed_hosts: list[str] = Field(
        default_factory=lambda: [
            "localhost",
            "127.0.0.1",
            "testserver",
            "backend",
        ]
    )
    cors_origins: list[str] = Field(default_factory=list)

    # SMTP - envio de comprobantes
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    smtp_from_name: str = "ERP Beauty Pro"
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False
    smtp_timeout_seconds: float = 15.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        if not self.is_production:
            return self

        if self.debug:
            raise ValueError("DEBUG debe ser false en producción.")

        if len(self.secret_key) < 32:
            raise ValueError(
                "SECRET_KEY debe contener al menos 32 caracteres "
                "en producción."
            )

        if not self.database_url.startswith("postgresql+psycopg://"):
            raise ValueError(
                "DATABASE_URL debe usar PostgreSQL con psycopg en producción."
            )

        if "*" in self.allowed_hosts:
            raise ValueError(
                "ALLOWED_HOSTS no puede contener '*' en producción."
            )

        if "*" in self.cors_origins:
            raise ValueError(
                "CORS_ORIGINS no puede contener '*' en producción."
            )

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
