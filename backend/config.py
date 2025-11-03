from pydantic_settings import BaseSettings
from typing import Optional
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    # Make GOOGLE_API_KEY optional during startup, but warn if missing
    GOOGLE_API_KEY: Optional[str] = None
    
    # Qdrant configuration - supports both local and cloud setups
    QDRANT_HOST: str = "localhost"  # Use "localhost" when running backend locally, "qdrant" in Docker
    QDRANT_PORT: int = 6333
    QDRANT_URL: Optional[str] = None  # For cloud setup, overrides host/port
    QDRANT_API_KEY: Optional[str] = None  # Optional for local setup
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra environment variables
    
    def validate_required_settings(self):
        """Validate that required settings are present when needed"""
        if not self.GOOGLE_API_KEY:
            logger.warning("GOOGLE_API_KEY is not set. Some features may not work properly.")
            logger.warning("Please set GOOGLE_API_KEY in your .env file or environment variables.")
            return False
        return True

# Initialize settings
try:
    settings = Settings()
    logger.info("Configuration loaded successfully")
    
    # Validate settings but don't fail startup
    settings.validate_required_settings()
    
except Exception as e:
    logger.error(f"Error loading configuration: {e}")
    # Create minimal settings for startup
    settings = Settings(GOOGLE_API_KEY=None)