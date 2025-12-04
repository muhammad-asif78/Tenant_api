# app/core/config.py
from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Multi-Tenant API"
    
    # Database
    # Provide a sensible default for local development. Override with env var in production.
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./tenant.db")
    
    # Security
    # WARNING: Replace the default SECRET_KEY in production using env var or .env.
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret")
    
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
        
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440))  # Default to 24 hours
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # First user (super admin) - for initial setup
    # Make optional so the app can start even when these env vars are not set.
    # Code that depends on these values should handle the None case.
    FIRST_SUPERUSER_EMAIL: Optional[str] = os.getenv("FIRST_SUPERUSER_EMAIL")
    FIRST_SUPERUSER_PASSWORD: Optional[str] = os.getenv("FIRST_SUPERUSER_PASSWORD")
    
    class Config:
        case_sensitive = True
        env_file = ".env"

# Create settings instance
settings = Settings()