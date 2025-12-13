"""Configuration management for SEC EDGAR Agent."""

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # OpenAI API
    openai_api_key: str = Field(
        default="",
        description="OpenAI API key",
    )
    anthropic_api_key: str = Field(
        default="",
        description="Anthropic API key",
    )
    openai_model: str = Field(
        default="gpt-4o",
        description="OpenAI model to use (e.g., gpt-4o, gpt-4-turbo, gpt-3.5-turbo)",
    )
    api_key: str = Field(
        default="sec-api-demo",
        description="API Key for ingestion endpoints",
    )

    # SEC EDGAR
    sec_user_agent: str = Field(
        default="SECEdgarAgent/0.1.0 (user@example.com)",
        description="User agent for SEC EDGAR API (required by SEC)",
    )
    sec_rate_limit: float = Field(
        default=10.0,
        description="Maximum requests per second to SEC EDGAR",
    )

    # Cache
    cache_ttl_seconds: int = Field(
        default=1800,
        description="Cache TTL in seconds (30 min default)",
    )
    cache_dir: Path = Field(
        default=Path("./data/cache"),
        description="Directory for filing cache",
    )

    # Vector store
    chroma_persist_dir: Path = Field(
        default=Path("./data/chroma"),
        description="Directory for ChromaDB persistence",
    )
    sqlite_db_path: Path = Field(
        default=Path("./data/sec_agent.db"),
        description="Path to SQLite database",
    )

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
        description="Logging level",
    )

    # API
    API_V1_STR: str = "/api/v1"

    # Agent settings
    max_agent_steps: int = Field(
        default=20,
        description="Maximum steps before agent terminates",
    )
    max_tool_retries: int = Field(
        default=3,
        description="Maximum retries for failed tool calls",
    )


# Global settings instance
settings = Settings()
