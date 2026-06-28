"""Tests for the tidy command."""

from typer.testing import CliRunner
from vibe_napkin.cli import app

runner = CliRunner()


def test_tidy_no_build_kb(tmp_project):
    """tidy gracefully handles missing build_kb.py."""
    result = runner.invoke(app, [
        "tidy", "--dir", str(tmp_project), "--yes",
    ])
    assert "zvec 未安装" in result.stdout or "build_kb" in result.stdout


def test_tidy_dry_run_no_build_kb(tmp_project):
    """tidy --dry-run also checks."""
    result = runner.invoke(app, [
        "tidy", "--dir", str(tmp_project), "--dry-run", "--yes",
    ])
    assert "zvec 未安装" in result.stdout or "build_kb" in result.stdout


def test_tidy_full_no_build_kb(tmp_project):
    """tidy --full also checks."""
    result = runner.invoke(app, [
        "tidy", "--dir", str(tmp_project), "--full", "--yes",
    ])
    assert "zvec 未安装" in result.stdout or "build_kb" in result.stdout