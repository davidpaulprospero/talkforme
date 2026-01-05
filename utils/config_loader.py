"""Configuration loader for Talk For Me."""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv


class ConfigLoader:
    """Loads configuration from .env and config.json files."""

    def __init__(self, project_root: str = "."):
        """
        Initialize config loader.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root)
        self._config: Dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        """Load all configuration sources."""
        # Load .env file if it exists
        env_path = self.project_root / ".env"
        if env_path.exists():
            load_dotenv(env_path)

        # Load config.json
        config_path = self.project_root / "config.json"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
        else:
            raise FileNotFoundError(
                f"config.json not found at {config_path}. "
                "Please create it from the template."
            )

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get config value by dot notation (e.g., 'audio.sample_rate').

        Args:
            key: Dot-separated key path
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def get_env(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get environment variable.

        Args:
            key: Environment variable name
            default: Default value if not found

        Returns:
            Environment variable value or default
        """
        return os.getenv(key, default)

    @property
    def config(self) -> Dict[str, Any]:
        """Get full config dictionary."""
        return self._config

    def __getitem__(self, key: str) -> Any:
        """Allow dict-like access to config."""
        return self.get(key)
