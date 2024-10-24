from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    API: str = "/api"
    PROJECT_NAME: str = "SN Analytics APP API"
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:8000"] # for local development only, change to frontend

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()