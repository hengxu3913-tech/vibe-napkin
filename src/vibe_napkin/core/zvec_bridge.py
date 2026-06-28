"""zvec vector database integration for vibe-napkin."""

from __future__ import annotations
from pathlib import Path
import subprocess
import shutil


def check_zvec_available() -> bool:
    """Check if zvec is installed and available on PATH."""
    return shutil.which("zvec") is not None


def sync_to_zvec(
    project_dir: Path,
    dry_run: bool = False,
) -> bool:
    """Sync business units to zvec vector store.

    Calls `zvec index --dir <docs_dir>`.
    Returns True on success, False on failure.
    """
    if not check_zvec_available():
        return False

    docs_dir = project_dir / "docs"
    if not docs_dir.exists():
        return False

    cmd = ["zvec", "index", "--dir", str(docs_dir)]
    if dry_run:
        cmd.append("--dry-run")

    try:
        result = subprocess.run(
            cmd, cwd=project_dir, capture_output=True, text=True, timeout=120,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False