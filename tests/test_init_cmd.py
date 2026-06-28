"""Tests for the init command."""

from typer.testing import CliRunner
from vibe_napkin.cli import app

runner = CliRunner()


def test_init_creates_structure(tmp_project):
    """init command creates expected directory structure."""
    result = runner.invoke(app, ["init", str(tmp_project)])
    assert result.exit_code == 0

    expected = [
        tmp_project / ".napkin" / "config.toml",
        tmp_project / "docs" / "README.md",
        tmp_project / "docs" / "业务单元" / "README.md",
        tmp_project / "docs" / "业务单元" / "_template.md",
        tmp_project / "docs" / "约束基线" / "README.md",
        tmp_project / "docs" / "约束基线" / "_baseline-技术约束.md",
    ]
    for path in expected:
        assert path.exists(), f"Missing: {path}"


def test_init_twice_is_safe(tmp_project):
    """Running init twice doesn't error."""
    runner.invoke(app, ["init", str(tmp_project)])
    result = runner.invoke(app, ["init", str(tmp_project)])
    assert result.exit_code == 0


def test_init_output_contains_success_message(tmp_project):
    """init output includes success message."""
    result = runner.invoke(app, ["init", str(tmp_project)])
    assert result.exit_code == 0
    assert "支桌子" in result.stdout


def test_init_with_project_name(tmp_project):
    """init with --name flag sets config project name."""
    runner.invoke(app, ["init", str(tmp_project), "--name", "my-app"])
    config_content = (tmp_project / ".napkin" / "config.toml").read_text()
    assert "my-app" in config_content