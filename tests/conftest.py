"""Shared test fixtures for vibe-napkin."""

import pytest
import tempfile
import shutil
import subprocess
from pathlib import Path


@pytest.fixture
def tmp_project():
    """Create a temporary directory simulating a project root."""
    tmp_dir = tempfile.mkdtemp()
    yield Path(tmp_dir)
    shutil.rmtree(tmp_dir)


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