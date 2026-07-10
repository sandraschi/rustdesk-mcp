"""
Configuration management for RustDeskMCP.
"""

import os
from pathlib import Path

from pydantic import DirectoryPath, Field, FilePath, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Application configuration."""

    # Server configuration
    host: str = Field("0.0.0.0", env="HOST")
    port: int = Field(10805, env="PORT")
    log_level: str = Field("INFO", env="LOG_LEVEL")

    # RustDesk configuration (optional for development)
    rustdesk_path: FilePath | None = Field(None, env="RUSTDESK_PATH")
    rustdesk_config_dir: DirectoryPath | None = Field(None, env="RUSTDESK_CONFIG_DIR")

    # RustDesk server configuration (direct socket communication)
    rustdesk_id_server_host: str = Field("127.0.0.1", env="RUSTDESK_ID_SERVER_HOST")
    rustdesk_id_server_port: int = Field(21116, env="RUSTDESK_ID_SERVER_PORT")
    rustdesk_relay_server_host: str = Field("127.0.0.1", env="RUSTDESK_RELAY_SERVER_HOST")
    rustdesk_relay_server_port: int = Field(21117, env="RUSTDESK_RELAY_SERVER_PORT")

    # Legacy API configuration (optional, for compatibility)
    rustdesk_api_url: str | None = Field(None, env="RUSTDESK_API_URL")
    rustdesk_api_key: str | None = Field(None, env="RUSTDESK_API_KEY")
    rustdesk_api_username: str = Field("admin", env="RUSTDESK_API_USERNAME")
    rustdesk_api_password: str = Field("", env="RUSTDESK_API_PASSWORD")

    # MCP configuration
    mcp_server_name: str = Field("RustDesk MCP Server", env="MCP_SERVER_NAME")
    mcp_server_description: str = Field(
        "FastMCP 2.10 server for RustDesk remote desktop management",
        env="MCP_SERVER_DESCRIPTION"
    )

    # Optional authentication
    auth_enabled: bool = Field(False, env="AUTH_ENABLED")
    auth_username: str | None = Field(None, env="AUTH_USERNAME")
    auth_password: str | None = Field(None, env="AUTH_PASSWORD")

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
    def validate_rustdesk_path(cls, v: str | None) -> Path | None:
        """Validate RustDesk executable path."""
        if v is None:
            # Try to auto-detect RustDesk installation
            default_paths = [
                r"C:\Program Files\RustDesk\rustdesk.exe",
                r"C:\Program Files (x86)\RustDesk\rustdesk.exe",
                r"C:\Users\{}\AppData\Local\RustDesk\rustdesk.exe".format(os.environ.get('USERNAME', '')),
                r"C:\Users\{}\AppData\Roaming\RustDesk\rustdesk.exe".format(os.environ.get('USERNAME', ''))
            ]

            for path_str in default_paths:
                path = Path(path_str).expanduser().resolve()
                if path.exists():
                    import logging
                    logging.getLogger(__name__).info(f"Auto-detected RustDesk at: {path}")
                    return path

            import logging
            logging.getLogger(__name__).warning("RustDesk executable not found in default locations")
            return None

        path = Path(v).expanduser().resolve()
        if not path.exists():
            import logging
            logging.getLogger(__name__).warning(f"RustDesk executable not found at: {path}")
        return path

    @field_validator("rustdesk_config_dir", mode="before")
    @classmethod
    def validate_rustdesk_config_dir(cls, v: str | None) -> Path | None:
        """Validate RustDesk config directory."""
        if v is None:
            # Try to auto-detect RustDesk config directory
            default_paths = [
                os.path.expandvars(r"%APPDATA%\RustDesk"),
                os.path.expandvars(r"%LOCALAPPDATA%\RustDesk"),
                r"C:\ProgramData\RustDesk",
            ]

            for path_str in default_paths:
                path = Path(path_str)
                if path.exists() and path.is_dir():
                    import logging
                    logging.getLogger(__name__).info(f"Auto-detected RustDesk config at: {path}")
                    return path

            # Create default config directory if none found
            default_config = Path(os.path.expandvars(r"%APPDATA%\RustDesk"))
            try:
                default_config.mkdir(parents=True, exist_ok=True)
                import logging
                logging.getLogger(__name__).info(f"Created default RustDesk config directory: {default_config}")
                return default_config
            except Exception:
                import logging
                logging.getLogger(__name__).warning(f"Could not create default config directory: {default_config}")
                return None

        path = Path(v).expanduser().resolve()
        if not path.exists():
            try:
                path.mkdir(parents=True, exist_ok=True)
            except Exception:
                # Don't fail if we can't create the directory
                import logging
                logging.getLogger(__name__).warning(f"Could not create RustDesk config directory: {path}")
        return path


# Global config instance
_config: Config | None = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config()  # type: ignore
    return _config
