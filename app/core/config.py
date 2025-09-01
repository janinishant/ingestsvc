from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Ingest Service"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = "Service for securely ingesting raw logs from fluent-bit log collector"
    
    # Server configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS settings
    ALLOWED_ORIGINS: List[str] = ["*"]
    
    # Database configuration
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_NAME: str = "dmart"
    DB_SCHEMA: str = "dev_demo"
    
    # Connection pool settings
    DB_POOL_MIN_SIZE: int = 10
    DB_POOL_MAX_SIZE: int = 20
    DB_POOL_MAX_QUERIES: int = 50000
    DB_POOL_MAX_INACTIVE_CONNECTION_LIFETIME: float = 300.0
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # Security
    SECRET_KEY: str = "your-secret-key-here"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()