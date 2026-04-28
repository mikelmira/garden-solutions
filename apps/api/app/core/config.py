from pydantic_settings import BaseSettings
from functools import lru_cache


# Default insecure key - only used in development
_DEV_SECRET_KEY = "INSECURE_DEV_SECRET_KEY_CHANGE_IN_PROD"


class Settings(BaseSettings):
    PROJECT_NAME: str = "Garden Solutions API"
    API_V1_STR: str = "/api/v1"

    # Environment: "development" or "production"
    ENVIRONMENT: str = "development"

    # Database
    # Railway/render provides DATABASE_URL — use it directly if set
    DATABASE_URL: str | None = None
    POSTGRES_USER: str = "admin"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "garden_solutions"
    SQLALCHEMY_DATABASE_URI: str | None = None

    # Auth - per docs: 15 min access token, 7 day refresh token
    # WARNING: In production, SECRET_KEY MUST be set via environment variable
    SECRET_KEY: str = _DEV_SECRET_KEY
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # Per docs: 15 minutes
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS - comma-separated list of allowed origins
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Schema version for JWT claims (for offline sync compatibility)
    SCHEMA_VERSION: int = 1

    # Shopify Integration (Pot Shack)
    SHOPIFY_SHOP_DOMAIN: str = ""  # e.g. "pot-shack.myshopify.com"
    SHOPIFY_ACCESS_TOKEN: str = ""  # Admin API access token
    SHOPIFY_WEBHOOK_SECRET: str = ""  # HMAC secret for webhook verification
    SHOPIFY_API_VERSION: str = "2024-01"

    def model_post_init(self, __context):
        if not self.SQLALCHEMY_DATABASE_URI:
            if self.DATABASE_URL:
                # Railway/Render provide DATABASE_URL — use directly
                self.SQLALCHEMY_DATABASE_URI = self.DATABASE_URL
            else:
                self.SQLALCHEMY_DATABASE_URI = (
                    f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                    f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
                )

        if self.ENVIRONMENT == "production":
            if not self.SECRET_KEY or self.SECRET_KEY == _DEV_SECRET_KEY:
                raise ValueError("SECRET_KEY must be set in production")

        if "*" in self.cors_origins_list:
            raise ValueError("CORS_ORIGINS cannot include '*'")

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS_ORIGINS into a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
