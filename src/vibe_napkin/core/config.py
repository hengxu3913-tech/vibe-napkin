"""Core configuration management for vibe-napkin."""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import tomlkit


@dataclass
class NapkinConfig:
    """vibe-napkin project configuration.

    Stored in .napkin/config.toml within the project directory.
    """

    embedding_provider: str = "local"
    embedding_api_key: str = ""
    zvec_data_dir: str = ".napkin/vectors"
    mcp_enabled: bool = True
    mcp_port: int = 8899
    project_name: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "NapkinConfig":
        """Create config from a nested dict (from TOML parse)."""
        return cls(
            embedding_provider=data.get("embedding", {}).get("provider", "local"),
            embedding_api_key=data.get("embedding", {}).get("api_key", ""),
            zvec_data_dir=data.get("zvec", {}).get("data_dir", ".napkin/vectors"),
            mcp_enabled=data.get("mcp", {}).get("enabled", True),
            mcp_port=data.get("mcp", {}).get("port", 8899),
            project_name=data.get("project", {}).get("name", ""),
        )

    def to_dict(self) -> dict:
        """Serialize config to a nested dict for TOML dump."""
        result = {
            "embedding": {
                "provider": self.embedding_provider,
            },
            "zvec": {
                "data_dir": self.zvec_data_dir,
            },
            "mcp": {
                "enabled": self.mcp_enabled,
                "port": self.mcp_port,
            },
            "project": {
                "name": self.project_name,
            },
        }
        if self.embedding_api_key:
            result["embedding"]["api_key"] = self.embedding_api_key
        return result


def get_napkin_dir(project_dir: Path) -> Path:
    """Get the .napkin directory, creating it if needed."""
    napkin_dir = project_dir / ".napkin"
    napkin_dir.mkdir(parents=True, exist_ok=True)
    return napkin_dir


def get_config_path(project_dir: Path) -> Path:
    """Get the path to .napkin/config.toml."""
    return get_napkin_dir(project_dir) / "config.toml"


def load_config(project_dir: Path) -> NapkinConfig:
    """Load config from .napkin/config.toml.

    Returns a NapkinConfig with defaults if no config file exists.
    """
    config_path = get_config_path(project_dir)
    if not config_path.exists():
        return NapkinConfig(project_name=project_dir.name)
    with open(config_path, "r", encoding="utf-8") as f:
        data = tomlkit.parse(f.read())
    config = NapkinConfig.from_dict(data)
    if not config.project_name:
        config.project_name = project_dir.name
    return config


def save_config(project_dir: Path, config: NapkinConfig) -> None:
    """Save config to .napkin/config.toml."""
    config_path = get_config_path(project_dir)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        tomlkit.dump(config.to_dict(), f)


def create_default_config(
    project_dir: Path,
    project_name: str = "",
    config: Optional[NapkinConfig] = None,
) -> NapkinConfig:
    """Create a default config file in .napkin/. Returns the config."""
    if config is not None:
        cfg = config
    else:
        cfg = NapkinConfig(project_name=project_name or project_dir.name)
    save_config(project_dir, cfg)
    return cfg