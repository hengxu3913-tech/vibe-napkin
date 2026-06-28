"""Tests for the wipe command."""

import subprocess
from pathlib import Path
from typer.testing import CliRunner
from vibe_napkin.cli import app

runner = CliRunner()


def _create_valid_unit(bu_dir: Path, name: str, content: str = ""):
    """Helper to create a valid business unit file."""
    if not content:
        content = f"""# {name}

## 关键词
test,关键词

## 业务规则
- 这是一个测试单元

## 代码位置
- test: `test.py::test` 1

## 关联业务单元


## 历史决策（近 3 次）
- 2026-01-01（a）：init

## 变更触发器
- none
"""
    fp = bu_dir / name
    fp.write_text(content)
    return fp


def test_wipe_with_no_changes(tmp_project_with_git):
    """wipe with no business units reports clean."""
    result = runner.invoke(app, ["wipe", "--dir", str(tmp_project_with_git)])
    assert result.exit_code == 0


def test_wipe_detects_new_unit(tmp_project_with_git):
    """wipe detects and processes a new business unit."""
    bu_dir = tmp_project_with_git / "docs" / "业务单元"
    bu_dir.mkdir(parents=True, exist_ok=True)
    _create_valid_unit(bu_dir, "001-test.md")

    result = runner.invoke(app, [
        "wipe", "--dir", str(tmp_project_with_git), "--yes",
    ])
    assert result.exit_code == 0
    assert "001-test.md" in result.stdout


def test_wipe_rejects_invalid_unit(tmp_project_with_git):
    """wipe blocks on invalid business unit format."""
    bu_dir = tmp_project_with_git / "docs" / "业务单元"
    bu_dir.mkdir(parents=True, exist_ok=True)
    unit_file = bu_dir / "bad-unit.md"
    unit_file.write_text("# Bad\n\nNo required sections here.")

    result = runner.invoke(app, [
        "wipe", "--dir", str(tmp_project_with_git), "--yes",
    ])
    assert result.exit_code != 0
    assert "缺少必填段" in result.stdout


def test_wipe_with_mixed_changes(tmp_project_with_git):
    """wipe handles mixed changes (new + invalid) gracefully."""
    bu_dir = tmp_project_with_git / "docs" / "业务单元"
    bu_dir.mkdir(parents=True, exist_ok=True)

    # Two units: one valid, one invalid
    _create_valid_unit(bu_dir, "good.md")
    (bu_dir / "bad.md").write_text("# Bad\n\nNo rules.")

    result = runner.invoke(app, [
        "wipe", "--dir", str(tmp_project_with_git), "--yes",
    ])
    assert result.exit_code != 0
    assert "缺少必填段" in result.stdout