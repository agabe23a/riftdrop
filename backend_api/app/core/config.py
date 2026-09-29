import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "RiftDrop API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-riftdrop-key-change-in-prod")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./riftdrop.db")

    # --- NEW: M-PESA DARAJA CREDENTIALS ---
    MPESA_CONSUMER_KEY: str = os.getenv("MPESA_CONSUMER_KEY", "your_sandbox_consumer_key")
    MPESA_CONSUMER_SECRET: str = os.getenv("MPESA_CONSUMER_SECRET", "your_sandbox_consumer_secret")
    MPESA_PASSKEY: str = os.getenv("MPESA_PASSKEY", "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919") # Default Safaricom Sandbox Passkey
    MPESA_SHORTCODE: str = os.getenv("MPESA_SHORTCODE", "174379")
    MPESA_ENVIRONMENT: str = os.getenv("MPESA_ENVIRONMENT", "sandbox") # 'sandbox' or 'production'

    class Config:
        case_sensitive = True

settings = Settings()