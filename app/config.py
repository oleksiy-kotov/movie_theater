from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # DB
    DATABASE_URL: str = "postgresql+asyncpg://admin:password@localhost:5432/movies_db"

    # JWT
    SECRET_KEY: str = "GXrxFAYGuV84aT9Ev0jI6MqT56ZiGJWj-SyJRd618sY"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Email
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@cinema.com"

    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLIC_KEY: str = ""

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    model_config = SettingsConfigDict(env_file=".env",)


settings = Settings()