"""Tests for API configuration security defaults."""

from unittest.mock import patch

import pytest
from pydantic import ValidationError

from src.api.config import DEFAULT_DEV_API_KEY, Settings


def build_settings_without_env_file() -> Settings:
    """Construct settings without loading a developer's local .env file."""
    return Settings(_env_file=None)


def test_production_rejects_missing_api_key() -> None:
    """Production startup fails when API_KEY is not configured."""
    with patch.dict("os.environ", {"ENVIRONMENT": "production"}, clear=True):
        with pytest.raises(ValidationError, match="API_KEY must be set"):
            build_settings_without_env_file()


def test_production_rejects_default_api_key() -> None:
    """Production startup fails when API_KEY uses the known development default."""
    with patch.dict(
        "os.environ",
        {"ENVIRONMENT": "production", "API_KEY": DEFAULT_DEV_API_KEY},
        clear=True,
    ):
        with pytest.raises(ValidationError, match="API_KEY must be set"):
            build_settings_without_env_file()


def test_production_uses_safe_cors_default() -> None:
    """Production has no wildcard CORS unless explicit safe origins are configured."""
    with patch.dict(
        "os.environ",
        {"ENVIRONMENT": "production", "API_KEY": "prod-secret-key"},
        clear=True,
    ):
        settings = build_settings_without_env_file()
        assert settings.CORS_ORIGINS == []


def test_production_rejects_wildcard_cors() -> None:
    """Wildcard CORS is rejected outside local/dev/test environments."""
    with patch.dict(
        "os.environ",
        {
            "ENVIRONMENT": "production",
            "API_KEY": "prod-secret-key",
            "CORS_ORIGINS": '["*"]',
        },
        clear=True,
    ):
        with pytest.raises(ValidationError, match="CORS_ORIGINS='\\*'"):
            build_settings_without_env_file()


def test_local_allows_development_defaults() -> None:
    """Local development keeps convenient defaults behind an explicit env flag."""
    with patch.dict("os.environ", {"ENVIRONMENT": "local"}, clear=True):
        settings = build_settings_without_env_file()
        assert settings.API_KEY == DEFAULT_DEV_API_KEY
        assert settings.CORS_ORIGINS == ["*"]


def test_cors_origins_accept_comma_separated_values() -> None:
    """CORS origins can be configured as a comma-separated environment variable."""
    with patch.dict(
        "os.environ",
        {
            "ENVIRONMENT": "production",
            "API_KEY": "prod-secret-key",
            "CORS_ORIGINS": "https://app.example.com, https://admin.example.com",
        },
        clear=True,
    ):
        settings = build_settings_without_env_file()
        assert settings.CORS_ORIGINS == [
            "https://app.example.com",
            "https://admin.example.com",
        ]


def test_cors_origins_accept_json_array_string() -> None:
    """CORS origins can be configured as a JSON array environment variable."""
    with patch.dict(
        "os.environ",
        {
            "ENVIRONMENT": "production",
            "API_KEY": "prod-secret-key",
            "CORS_ORIGINS": '  ["https://app.example.com"]  ',
        },
        clear=True,
    ):
        settings = build_settings_without_env_file()
        assert settings.CORS_ORIGINS == ["https://app.example.com"]


def test_settings_normalize_environment_and_api_key() -> None:
    """Settings expose normalized runtime values after validation."""
    with patch.dict(
        "os.environ",
        {
            "ENVIRONMENT": " Production ",
            "API_KEY": " prod-secret-key ",
        },
        clear=True,
    ):
        settings = build_settings_without_env_file()
        assert settings.ENVIRONMENT == "production"
        assert settings.API_KEY == "prod-secret-key"
