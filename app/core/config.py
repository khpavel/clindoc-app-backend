import os
import logging
from pydantic_settings import BaseSettings
from pydantic import ValidationError

logger = logging.getLogger(__name__)


def _get_env_file_list() -> list[str]:
    """
    Determine which .env files to load based on APP_ENV environment variable.
    
    To switch environments, set APP_ENV environment variable:
    - Windows PowerShell: $env:APP_ENV="prod"
    - Windows CMD: set APP_ENV=prod
    - Linux/Mac: export APP_ENV=prod
    
    Or set it in your shell/IDE before running the application.
    
    Files are loaded in order, with later files overriding earlier ones:
    - For dev: [".env.dev", ".env"] (if .env exists, it overrides .env.dev)
    - For prod: [".env.prod", ".env"] (if .env exists, it overrides .env.prod)
    """
    # Read APP_ENV from actual environment variable (not from .env file)
    # This allows us to determine which .env file to load
    app_env = os.environ.get("APP_ENV", "dev").lower()
    
    if app_env == "prod":
        return [".env.prod", ".env"]
    else:  # default to dev
        return [".env.dev", ".env"]


class Settings(BaseSettings):
    app_env: str = "dev"  # Environment name (dev/prod), can be overridden via APP_ENV env var
    database_url: str
    
    # JWT Authentication settings
    secret_key: str  # SECRET_KEY - used for signing JWT tokens
    algorithm: str = "HS256"  # ALGORITHM - JWT signing algorithm
    access_token_expire_minutes: int = 60  # ACCESS_TOKEN_EXPIRE_MINUTES - token expiration time
    
    # Storage settings
    storage_dir: str = "storage"  # STORAGE_DIR - base directory for uploaded source documents
    
    # AI settings
    ai_mode: str = "stub"  # AI_MODE - AI implementation mode: "stub" or "real"

    class Config:
        env_file = _get_env_file_list()
        env_prefix = ""
        case_sensitive = False
        extra = "ignore"


try:
    settings = Settings()
except ValidationError as e:
    env_files = _get_env_file_list()
    missing_files = [f for f in env_files if not os.path.exists(f)]
    logger.error(
        f"Failed to load settings. Missing required environment variables. "
        f"Required: database_url, secret_key. "
        f"Looking for env files: {env_files}. "
        f"Missing files: {missing_files}. "
        f"Error details: {e}"
    )
    raise
except Exception as e:
    logger.error(f"Unexpected error loading settings: {e}", exc_info=True)
    raise
