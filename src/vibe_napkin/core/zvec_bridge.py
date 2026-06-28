"""zvec MCP integration — calls the real build_kb.py from .napkin/mcp/."""

from __future__ import annotations
from pathlib import Path
import subprocess
import sys


def check_build_kb_script(project_dir: Path) -> bool:
    """Check if .napkin/mcp/build_kb.py exists."""
    return (project_dir / ".napkin" / "mcp" / "build_kb.py").exists()


def sync_to_zvec(
    project_dir: Path,
    dry_run: bool = False,
    full_rebuild: bool = False,
) -> bool:
    """Sync business units to zvec vector store via build_kb.py.

    Calls: python .napkin/mcp/build_kb.py [--dry-run] [--full]
    Returns True on success, False on failure.
    """
    build_kb = project_dir / ".napkin" / "mcp" / "build_kb.py"
    if not build_kb.exists():
        return False

    cmd = [sys.executable, str(build_kb)]
    if full_rebuild:
        cmd.append("--full")
    elif dry_run:
        cmd.append("--dry-run")

    try:
        result = subprocess.run(
            cmd, cwd=build_kb.parent,
            capture_output=True, text=True, timeout=300,
        )
        print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("❌ zvec build 超时（5分钟）", flush=True)
        return False
    except FileNotFoundError:
        return False


def check_zvec_available(project_dir: Path) -> bool:
    """Check if zvec library is importable and build_kb.py exists."""
    try:
        import zvec  # noqa: F401
        return check_build_kb_script(project_dir)
    except ImportError:
        return False


def check_zvec_installed() -> bool:
    """Check if zvec pip package is installed (backward compat)."""
    try:
        import zvec  # noqa: F401
        return True
    except ImportError:
        return False