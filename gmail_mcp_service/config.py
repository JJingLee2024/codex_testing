"""Configuration helpers for the Gmail MCP service."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import BaseSettings, Field, validator


class Settings(BaseSettings):
    """Runtime configuration for the service.

    Values are pulled from environment variables or a ``.env`` file if present.
    """

    google_client_secret_file: Path = Field(
        ..., env="GOOGLE_CLIENT_SECRET_FILE", description="Path to the OAuth client secret JSON file"
    )
    gmail_token_file: Path = Field(
        default=Path("token.json"), env="GMAIL_TOKEN_FILE", description="Path to the OAuth token JSON file"
    )
    gmail_user_id: str = Field(default="me", env="GMAIL_USER_ID")
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", env="OPENAI_MODEL")
    allowed_senders: Optional[str] = Field(
        default=None,
        env="ALLOWED_SENDERS",
        description="Comma separated list of email addresses that are allowed to be processed. If not set all messages are allowed.",
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @validator("google_client_secret_file", "gmail_token_file", pre=True)
    def _expand_path(cls, value: str | Path) -> Path:
        return Path(value).expanduser().resolve()

    @property
    def allowed_senders_list(self) -> list[str] | None:
        if not self.allowed_senders:
            return None
        return [item.strip().lower() for item in self.allowed_senders.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return the cached :class:`Settings` instance."""

    return Settings()
