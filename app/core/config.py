from typing import Dict, List, Optional, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings.
    
    These settings can be configured using environment variables.
    """
    PROJECT_NAME: str = "Volitas Backend"
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = "development"
    
    # CORS settings - use string list to avoid URL validation issues
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173", 
        "http://localhost:4173", 
        "http://localhost:5174", 
        "http://localhost:5175", 
        "http://localhost:5176"
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            # Handle comma-separated string from environment variables
            if v.strip():
                return [i.strip() for i in v.split(",") if i.strip()]
            return []
        elif isinstance(v, list):
            return v
        return []

    # Database settings - support both old format and new DATABASE_URL
    DATABASE_URL: Optional[str] = None
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "volitas"
    DATABASE_URI: Optional[str] = None  # Legacy support

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        # Prefer DATABASE_URL if set
        if self.DATABASE_URL:
            return self.DATABASE_URL
        # Fall back to DATABASE_URI (legacy)
        if self.DATABASE_URI:
            return self.DATABASE_URI
        # Build from components
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Redis settings - support both old format and new REDIS_URL
    REDIS_URL: Optional[str] = None
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    @property
    def REDIS_URI(self) -> str:
        # Prefer REDIS_URL if set
        if self.REDIS_URL:
            return self.REDIS_URL
        # Build from components
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # Supabase settings
    SUPABASE_URL: Optional[str] = None
    SUPABASE_SERVICE_KEY: Optional[str] = None
    
    # Stripe settings
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    
    # Frontend URL for redirects
    FRONTEND_URL: str = "http://localhost:5173"
    
    # Cache settings - disable by default in production if no Redis URL
    CACHE_ENABLED: bool = True
    CACHE_DEFAULT_TIMEOUT: int = 300  # 5 minutes
    
    @property
    def CACHE_ACTUALLY_ENABLED(self) -> bool:
        """Check if cache should actually be enabled based on environment and Redis availability."""
        if not self.CACHE_ENABLED:
            return False
        # In production, only enable cache if Redis URL is explicitly provided
        if self.ENVIRONMENT == "production":
            return bool(self.REDIS_URL)
        return True
    
    # Market data settings
    MARKET_DATA_UPDATE_INTERVAL: int = 60  # seconds
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        case_sensitive = True
        env_file = ".env"


# Create global settings instance
settings = Settings()
