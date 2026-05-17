"""API configuration settings loaded from environment and defaults."""
import logging
import sys
from typing import Any

import structlog
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_DEV_API_KEY = "sec-api-demo"
LOCAL_ENVIRONMENTS = {"local", "dev", "development", "test", "testing"}


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
    ENVIRONMENT: str = Field(
        default="production",
        description="Runtime environment: local/dev/test allow development defaults",
    )
    CORS_ORIGINS: list[str] | str = Field(
        default="",
        description="Allowed CORS origins. Wildcard is only allowed in local/dev/test.",
    )

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
        default=DEFAULT_DEV_API_KEY,
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

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> Any:
        """Support comma-separated CORS origins in addition to JSON arrays."""
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return []
            if stripped.startswith("["):
                return value
            return [origin.strip() for origin in stripped.split(",") if origin.strip()]
        return value

    @model_validator(mode="after")
    def validate_security_defaults(self) -> "Settings":
        """Reject development security defaults outside local/dev/test."""
        environment = self.ENVIRONMENT.strip().lower()
        is_local_environment = environment in LOCAL_ENVIRONMENTS
        api_key = self.API_KEY.strip()

        if not is_local_environment and api_key in {"", DEFAULT_DEV_API_KEY}:
            raise ValueError(
                "API_KEY must be set to a non-default value when ENVIRONMENT is not "
                "local, dev, or test."
            )

        if isinstance(self.CORS_ORIGINS, str):
            self.CORS_ORIGINS = self.parse_cors_origins(self.CORS_ORIGINS)

        if not self.CORS_ORIGINS and is_local_environment:
            self.CORS_ORIGINS = ["*"]

        if not is_local_environment and "*" in self.CORS_ORIGINS:
            raise ValueError(
                "CORS_ORIGINS='*' is only allowed when ENVIRONMENT is local, dev, "
                "or test. Configure explicit production origins instead."
            )

        return self

settings = Settings()


def configure_logging() -> None:
    """Configure structured logging with structlog."""
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if settings.DEBUG:
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(),
        ]
    else:
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(
        processors=processors,
        logger_factory=structlog.PrintLoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )

    #Redirect standard logging to structlog
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=logging.INFO)

    # Silence noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
