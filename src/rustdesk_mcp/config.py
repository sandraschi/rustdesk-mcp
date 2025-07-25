""
Configuration management for RustDeskMCP.
"""

import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator, DirectoryPath, FilePath


class Config(BaseSettings):
    """Application configuration."""

    # Server configuration
    host: str = Field("0.0.0.0", env="HOST")
    port: int = Field(8077, env="PORT")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    # RustDesk configuration
    rustdesk_path: FilePath = Field(..., env="RUSTDESK_PATH")
    rustdesk_config_dir: DirectoryPath = Field(..., env="RUSTDESK_CONFIG_DIR")
    
    # MCP configuration
    mcp_server_name: str = Field("RustDesk MCP Server", env="MCP_SERVER_NAME")
    mcp_server_description: str = Field(
        "FastMCP 2.10 server for RustDesk remote desktop management",
        env="MCP_SERVER_DESCRIPTION"
    )
    
    # Optional authentication
    auth_enabled: bool = Field(False, env="AUTH_ENABLED")
    auth_username: Optional[str] = Field(None, env="AUTH_USERNAME")
    auth_password: Optional[str] = Field(None, env="AUTH_PASSWORD")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level. Must be one of: {', '.join(valid_levels)}")
        return v.upper()
    
    @field_validator("rustdesk_path", mode="before")
    @classmethod
    def validate_rustdesk_path(cls, v: str) -> Path:
        """Validate RustDesk executable path."""
        path = Path(v).expanduser().resolve()
        if not path.exists():
            raise ValueError(f"RustDesk executable not found at: {path}")
        return path
    
    @field_validator("rustdesk_config_dir", mode="before")
    @classmethod
    def validate_rustdesk_config_dir(cls, v: str) -> Path:
        """Validate RustDesk config directory."""
        path = Path(v).expanduser().resolve()
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
        return path


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config()  # type: ignore
    return _config
