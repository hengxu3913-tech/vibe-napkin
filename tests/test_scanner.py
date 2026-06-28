"""Tests for the scanner module."""

import subprocess
from vibe_napkin.core.scanner import (
    scan_business_units,
    ChangeType,
    get_business_unit_dir,
)


def test_scan_new_file(tmp_project_with_git):
    """New business unit file detected as ADDED."""
    bu_dir = get_business_unit_dir(tmp_project_with_git)
    bu_dir.mkdir(parents=True, exist_ok=True)
    new_file = bu_dir / "001-test-unit.md"
    new_file.write_text("# Test\n## 关键词\na\n## 业务规则\nb")

    changes = scan_business_units(tmp_project_with_git)
    assert len(changes) == 1
    assert changes[0].change_type == ChangeType.ADDED
    assert changes[0].file_path == new_file


def test_scan_modified_file(tmp_project_with_git):
    """Modified business unit file detected as MODIFIED."""
    bu_dir = get_business_unit_dir(tmp_project_with_git)
    bu_dir.mkdir(parents=True, exist_ok=True)
    existing = bu_dir / "001-test-unit.md"
    existing.write_text("# Original\n## 关键词\na\n## 业务规则\nb")

    subprocess.run(["git", "add", "."], cwd=tmp_project_with_git, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "add business unit"],
        cwd=tmp_project_with_git, capture_output=True,
    )

    # Modify the file
    existing.write_text("# Modified\n## 关键词\na,b\n## 业务规则\nnew rule")

    changes = scan_business_units(tmp_project_with_git)
    modified = [c for c in changes if c.change_type == ChangeType.MODIFIED]
    assert len(modified) == 1


def test_scan_no_changes(tmp_project_with_git):
    """No changes returns empty list."""
    changes = scan_business_units(tmp_project_with_git)
    assert len(changes) == 0


def test_scan_without_git(tmp_project):
    """Without git, scanner falls back to file hash comparison."""
    bu_dir = get_business_unit_dir(tmp_project)
    bu_dir.mkdir(parents=True, exist_ok=True)
    unit_file = bu_dir / "001-test.md"
    unit_file.write_text("# Test\n## 关键词\na\n## 业务规则\nb")

    changes = scan_business_units(tmp_project)
    added = [c for c in changes if c.change_type == ChangeType.ADDED]
    assert len(added) == 1


def test_scanner_skips_readme_and_template(tmp_project_with_git):
    """README.md and _template.md are skipped by scanner."""
    bu_dir = get_business_unit_dir(tmp_project_with_git)
    bu_dir.mkdir(parents=True, exist_ok=True)
    (bu_dir / "README.md").write_text("# Readme")
    (bu_dir / "_template.md").write_text("# Template")

    changes = scan_business_units(tmp_project_with_git)
    assert len(changes) == 0