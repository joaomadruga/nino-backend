from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database settings
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/chatbot"

    # Redis settings
    redis_url: str = "redis://localhost:6379"

    # Model settings
    model_name: str = "Jurema-br/Jurema-7B"
    max_new_tokens: int = 512

    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False

    # Hugging Face settings
    huggingface_hub_token: Optional[str] = None

    class Config:
        env_file = ".env"


settings = Settings()