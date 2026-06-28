"""Tests for the config module."""

from pathlib import Path
from vibe_napkin.core.config import (
    NapkinConfig,
    load_config,
    save_config,
    create_default_config,
    get_config_path,
)


def test_load_config_returns_defaults_when_no_file(tmp_project):
    """Loading config from a dir without .napkin/config.toml returns defaults."""
    config = load_config(tmp_project)
    assert isinstance(config, NapkinConfig)
    assert config.embedding_provider == "aliyun"


def test_create_and_load_config(tmp_project):
    """Create default config, then load it back."""
    create_default_config(tmp_project, project_name="my-test")
    config_path = get_config_path(tmp_project)
    assert config_path.exists()
    loaded = load_config(tmp_project)
    assert loaded.project_name == "my-test"
    assert loaded.embedding_provider in ("aliyun", "local", "openai")


def test_config_roundtrip(tmp_project):
    """Modify and save config, verify fields persist."""
    config = NapkinConfig(
        embedding_provider="openai",
        embedding_api_key="sk-test123",
        embedding_model="text-embedding-3-small",
        embedding_dim=1536,
        embedding_base_url="https://api.openai.com/v1",
        project_name="test-proj",
    )
    create_default_config(tmp_project, config=config)
    loaded = load_config(tmp_project)
    assert loaded.embedding_provider == "openai"
    assert loaded.embedding_api_key == "sk-test123"
    assert loaded.embedding_model == "text-embedding-3-small"
    assert loaded.embedding_dim == 1536
    assert loaded.embedding_base_url == "https://api.openai.com/v1"
    assert loaded.project_name == "test-proj"


def test_config_to_dict_omits_empty_api_key(tmp_project):
    """Empty api_key should not appear in serialized output."""
    config = NapkinConfig(embedding_provider="local")
    d = config.to_dict()
    assert "api_key" not in d["embedding"]


def test_config_to_dict_includes_key_when_set(tmp_project):
    """api_key appears when set."""
    config = NapkinConfig(embedding_api_key="sk-abc")
    d = config.to_dict()
    assert d["embedding"]["api_key"] == "sk-abc"