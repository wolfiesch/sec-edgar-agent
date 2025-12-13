"""API configuration settings loaded from environment and defaults."""
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration for the FastAPI layer and related services."""
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )

    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "SEC API for LLMs"
    VERSION: str = "0.1.0"
    CORS_ORIGINS: list[str] = ["*"]

    # Validation settings
    DEBUG: bool = False

    SEC_USER_AGENT: str = "SECEdgarAgent/0.1.0 (unknown@example.com)"

    # Rate limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = Field(
        default=60,
        description="Maximum requests per minute per IP"
    )
    RATE_LIMIT_REQUESTS_PER_HOUR: int = Field(
        default=1000,
        description="Maximum requests per hour per IP"
    )

    # API Key (loaded from global settings, but can be overridden)
    API_KEY: str = Field(
        default="sec-api-demo",
        description="API key for protected endpoints"
    )

    # OpenAI settings for chat endpoint
    OPENAI_API_KEY: str = Field(
        default="",
        description="OpenAI API key for chat completions"
    )
    OPENAI_MODEL: str = Field(
        default="gpt-4o-mini",
        description="OpenAI model to use for chat"
    )

settings = Settings()
