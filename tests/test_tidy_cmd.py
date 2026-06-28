"""Tests for the tidy command."""

from typer.testing import CliRunner
from vibe_napkin.cli import app

runner = CliRunner()


def test_tidy_no_zvec(tmp_project):
    """tidy gracefully handles missing zvec."""
    result = runner.invoke(app, [
        "tidy", "--dir", str(tmp_project), "--yes",
    ])
    assert "zvec 未安装" in result.stdout


def test_tidy_dry_run_without_zvec(tmp_project):
    """tidy --dry-run also checks for zvec."""
    result = runner.invoke(app, [
        "tidy", "--dir", str(tmp_project), "--dry-run", "--yes",
    ])
    assert "zvec 未安装" in result.stdout