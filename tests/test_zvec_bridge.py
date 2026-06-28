"""Tests for the zvec bridge module."""

from pathlib import Path
from vibe_napkin.core.zvec_bridge import (
    check_zvec_available,
    check_build_kb_script,
    check_zvec_installed,
)


def test_zvec_installed_check():
    """check_zvec_installed returns True/False (False in test env)."""
    # This checks the pip package, should work in env where zvec isn't installed
    result = check_zvec_installed()
    assert isinstance(result, bool)


def test_check_build_kb_script_missing(tmp_project):
    """build_kb.py check returns False when .napkin/mcp/ doesn't exist."""
    assert check_build_kb_script(tmp_project) is False


def test_check_build_kb_script_exists(tmp_project):
    """build_kb.py check returns True when file exists."""
    mcp_dir = tmp_project / ".napkin" / "mcp"
    mcp_dir.mkdir(parents=True, exist_ok=True)
    (mcp_dir / "build_kb.py").write_text("# fake")
    assert check_build_kb_script(tmp_project) is True


def test_zvec_available_without_build_kb(tmp_project):
    """check_zvec_available returns False without build_kb.py."""
    assert check_zvec_available(tmp_project) is False