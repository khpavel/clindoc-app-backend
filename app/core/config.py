import os
from pydantic_settings import BaseSettings


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

    class Config:
        env_file = _get_env_file_list()
        env_prefix = ""
        case_sensitive = False
        extra = "ignore"


settings = Settings()
