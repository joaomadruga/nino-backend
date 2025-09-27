from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os


class Settings(BaseSettings):
    # Database settings
    database_url: str = Field(default="postgresql+asyncpg://postgres:password@localhost:5432/chatbot")

    # Model settings
    model_name: str = Field(default="Jurema-br/Jurema-7B")
    max_new_tokens: int = Field(default=1024)

    # API settings
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default_factory=lambda: int(os.getenv("PORT", "8000")))
    debug: bool = Field(default=False)

    # Hugging Face settings
    huggingface_hub_token: Optional[str] = Field(default=None)

    class Config:
        env_file = ".env"


settings = Settings()