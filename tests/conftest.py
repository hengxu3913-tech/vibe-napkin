"""Shared test fixtures for vibe-napkin."""

import pytest
import tempfile
import shutil
import subprocess
import os
import stat
from pathlib import Path


def _remove_readonly(func, path, _):
    """Clear read-only bit and retry deletion (handles Windows git locks)."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


@pytest.fixture
def tmp_project():
    """Create a temporary directory simulating a project root."""
    tmp_dir = tempfile.mkdtemp()
    yield Path(tmp_dir)
    shutil.rmtree(tmp_dir, onerror=_remove_readonly)


@pytest.fixture
def tmp_project_with_git(tmp_project):
    """Create a temp project with git initialized and an initial commit."""
    subprocess.run(["git", "init"], cwd=tmp_project, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=tmp_project, capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Tester"],
        cwd=tmp_project, capture_output=True,
    )
    (tmp_project / "README.md").write_text("# Test")
    subprocess.run(["git", "add", "."], cwd=tmp_project, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "init"],
        cwd=tmp_project, capture_output=True,
    )
    return tmp_project