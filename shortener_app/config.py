from functools import lru_cache
from pydantic import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()


class Settings(BaseSettings):
    env_name: str = "Local"
    base_url: str = os.environ.get('BASE_URL')
    db_url: str = os.environ.get('DATABASE_URI')

    class Config:
        env_file = "../venv/.env"


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    print(f"Loading settings for: {settings.env_name}")
    return settings
