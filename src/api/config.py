from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )

    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "SEC API for LLMs"
    VERSION: str = "0.1.0"
    CORS_ORIGINS: List[str] = ["*"]

    # Validation settings
    DEBUG: bool = False

    SEC_USER_AGENT: str = "SECEdgarAgent/0.1.0 (unknown@example.com)"

settings = Settings()
