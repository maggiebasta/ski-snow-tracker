from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Dict, Optional

class Settings(BaseSettings):
    # API Credentials
    weather_unlocked_app_id: str = ""
    weather_unlocked_api_key: str = ""
    
    # Database Configuration
    database_url: str = "postgresql://postgres:password@localhost:5432/postgres"  # Default fallback
    env: str = "production"  # Default to production
    debug: bool = False

    @property
    def is_production(self) -> bool:
        return self.env.lower() == "production"
    
    @property
    def database_connection_args(self) -> Dict:
        """Get database connection arguments based on environment."""
        if self.is_production:
            return {
                "sslmode": "require",
                "connect_timeout": 30,
                "keepalives": 1,
                "keepalives_idle": 30,
                "keepalives_interval": 10,
                "keepalives_count": 5
            }
        return {}

    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    return Settings()
