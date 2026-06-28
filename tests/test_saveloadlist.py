"""Tests for save, load, and list commands."""

from typer.testing import CliRunner
from vibe_napkin.cli import app

runner = CliRunner()


def test_save_creates_checkpoint(tmp_project_with_git):
    """save command creates a checkpoint file."""
    result = runner.invoke(app, [
        "save", "--dir", str(tmp_project_with_git), "--label", "测试存档",
    ])
    assert result.exit_code == 0
    assert "存档成功" in result.stdout
    ckpt_dir = tmp_project_with_git / ".napkin" / "checkpoints"
    json_files = list(ckpt_dir.glob("*.json"))
    assert len(json_files) >= 1


def test_save_and_load(tmp_project_with_git):
    """save then load returns context."""
    # Save
    result = runner.invoke(app, [
        "save", "--dir", str(tmp_project_with_git), "--label", "存档测试",
    ])
    assert result.exit_code == 0

    # Find the checkpoint ID
    ckpt_dir = tmp_project_with_git / ".napkin" / "checkpoints"
    json_files = sorted(ckpt_dir.glob("*.json"))
    assert len(json_files) >= 1
    ckpt_id = json_files[0].stem

    # Load
    result = runner.invoke(app, [
        "load", "--dir", str(tmp_project_with_git), ckpt_id,
    ])
    assert result.exit_code == 0
    assert "存档测试" in result.stdout or "读档" in result.stdout


def test_load_nonexistent(tmp_project):
    """Loading non-existent checkpoint reports error."""
    result = runner.invoke(app, [
        "load", "--dir", str(tmp_project), "non-existent-id",
    ])
    assert result.exit_code != 0
    assert "未找到" in result.stdout


def test_list_shows_checkpoints(tmp_project_with_git):
    """list command shows all checkpoints."""
    runner.invoke(app, [
        "save", "--dir", str(tmp_project_with_git), "--label", "存档1",
    ])
    runner.invoke(app, [
        "save", "--dir", str(tmp_project_with_git), "--label", "存档2",
    ])

    result = runner.invoke(app, ["list", "--dir", str(tmp_project_with_git)])
    assert result.exit_code == 0
    assert "存档1" in result.stdout
    assert "存档2" in result.stdout


def test_list_empty(tmp_project):
    """list with no checkpoints shows appropriate message."""
    result = runner.invoke(app, ["list", "--dir", str(tmp_project)])
    assert result.exit_code == 0
    assert "暂无存档" in result.stdout