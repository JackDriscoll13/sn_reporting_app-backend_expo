from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    API: str = "/api"
    PROJECT_NAME: str = "Engagement Analytics API"
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()