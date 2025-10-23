from pydantic_settings import BaseSettings
from typing import Optional, List
from zoneinfo import ZoneInfo
import os


class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str
    PROJECT_NAME: str

    # Database Configuration
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # Llama/Ollama Settings
    OLLAMA_HOST: str
    OLLAMA_MODEL: str

    # File Upload Settings
    UPLOAD_DIR: str
    MAX_FILE_SIZE: int
    ALLOWED_EXTENSIONS: set = {".pdf", ".png", ".jpg", ".jpeg"}

    # Timezone
    TIMEZONE: str

    @property
    def TZ(self) -> ZoneInfo:
        return ZoneInfo(self.TIMEZONE)

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost", "http://localhost:8080", "http://localhost:3000"]

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
