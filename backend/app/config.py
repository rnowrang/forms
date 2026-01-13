"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database (defaults to SQLite for local dev, use PostgreSQL in production)
    database_url: str = "sqlite:///./irb_forms.db"
    
    # Authentication
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 hours
    
    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    
    # File storage paths (relative for local dev)
    upload_dir: str = "./storage/uploads"
    generated_dir: str = "./storage/generated"
    template_dir: str = "./storage/templates"
    
    # LibreOffice
    libreoffice_path: str = "/usr/bin/soffice"
    
    # Debug mode
    debug: bool = True
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
