"""Tests for configuration."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.config import Settings


class TestSettings:
    """Tests for Settings configuration."""

    def test_settings_defaults(self) -> None:
        """Test default settings values."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}, clear=True):
            settings = Settings()
            assert settings.openai_api_key == "test-key"
            assert settings.openai_model == "gpt-4o"
            assert settings.cache_ttl_seconds == 1800
            assert settings.log_level == "INFO"
            assert settings.max_agent_steps == 20

    def test_settings_custom_values(self) -> None:
        """Test custom settings from environment."""
        with patch.dict(
            "os.environ",
            {
                "OPENAI_API_KEY": "custom-key",
                "OPENAI_MODEL": "gpt-4-turbo",
                "CACHE_TTL_SECONDS": "3600",
                "LOG_LEVEL": "DEBUG",
                "MAX_AGENT_STEPS": "50",
                "SEC_USER_AGENT": "TestAgent/1.0",
            },
            clear=True,
        ):
            settings = Settings()
            assert settings.openai_api_key == "custom-key"
            assert settings.openai_model == "gpt-4-turbo"
            assert settings.cache_ttl_seconds == 3600
            assert settings.log_level == "DEBUG"
            assert settings.max_agent_steps == 50
            assert settings.sec_user_agent == "TestAgent/1.0"

    def test_cache_dir_creation(self) -> None:
        """Test that cache_dir is properly set."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}, clear=True):
            settings = Settings()
            assert isinstance(settings.cache_dir, Path)
            assert "cache" in str(settings.cache_dir)

    def test_chroma_persist_dir(self) -> None:
        """Test chroma persist directory setting."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}, clear=True):
            settings = Settings()
            assert isinstance(settings.chroma_persist_dir, Path)
            assert "chroma" in str(settings.chroma_persist_dir)

    def test_custom_cache_dir(self) -> None:
        """Test custom cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(
                "os.environ",
                {
                    "OPENAI_API_KEY": "test-key",
                    "CACHE_DIR": tmpdir,
                },
                clear=True,
            ):
                settings = Settings()
                assert str(settings.cache_dir) == tmpdir

    def test_default_api_key(self) -> None:
        """Test default API key when not set."""
        with patch.dict("os.environ", {}, clear=True):
            settings = Settings()
            assert settings.openai_api_key == ""  # Has default empty string
