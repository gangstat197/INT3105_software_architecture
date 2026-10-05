from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str

    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = ""

    LEITNER_INTERVALS: tuple[int, ...] = (1, 3, 7, 14, 30)
    LEITNER_BOX_COUNT: int = 5

    model_config = SettingsConfigDict(
        extra="ignore",
    )

settings = Settings()