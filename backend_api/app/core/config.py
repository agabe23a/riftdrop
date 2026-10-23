from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")
    ENVIRONMENT: Literal["development", "test", "production"] = "development"
    PROJECT_NAME: str = "RiftDrop API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "super-secret-riftdrop-key-change-in-prod"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15, ge=5, le=1440)
    DATABASE_URL: str = "sqlite+aiosqlite:///./riftdrop.db"
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    SQL_ECHO: bool = False
    MPESA_CONSUMER_KEY: str | None = None
    MPESA_CONSUMER_SECRET: str | None = None
    MPESA_PASSKEY: str | None = None
    MPESA_SHORTCODE: str | None = None
    MPESA_ENVIRONMENT: Literal["sandbox", "production"] = "sandbox"
    MPESA_CALLBACK_URL: str | None = None
    CLOUDINARY_CLOUD_NAME: str | None = None
    CLOUDINARY_API_KEY: str | None = None
    CLOUDINARY_API_SECRET: str | None = None
    SMTP_HOST: str | None = None
    SMTP_PORT: int = Field(default=587, ge=1, le=65535)
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM: str | None = None
    SMTP_STARTTLS: bool = True

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @model_validator(mode="after")
    def validate_production_settings(self):
        if self.ENVIRONMENT == "production" and self.SECRET_KEY == "super-secret-riftdrop-key-change-in-prod":
            raise ValueError("SECRET_KEY must be set to a strong unique value in production")
        if self.ENVIRONMENT == "production" and not self.MPESA_CALLBACK_URL:
            raise ValueError("MPESA_CALLBACK_URL is required in production")
        if self.ENVIRONMENT == "production" and (not self.SMTP_HOST or not self.SMTP_FROM):
            raise ValueError("SMTP_HOST and SMTP_FROM are required in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
