from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Corrector de Documentos"

    # Database
    DATABASE_URL: str = "mysql+pymysql://root:password@db:3306/corrector_despa"

    # Llama/Ollama Settings
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "phi4"

    # File Upload Settings
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: set = {".pdf", ".png", ".jpg", ".jpeg"}

    # CORS
    BACKEND_CORS_ORIGINS: list = ["http://localhost", "http://localhost:8080", "http://localhost:3000"]

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
