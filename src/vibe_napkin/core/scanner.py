"""Change detection for business unit files.

Uses git status --porcelain when available (handles UTF-8 paths on all platforms),
falls back to file hash comparison.
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List
import hashlib
import json
import subprocess
import os


class ChangeType(Enum):
    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"


@dataclass
class FileChange:
    file_path: Path
    change_type: ChangeType
    relative_path: str = ""


def get_business_unit_dir(project_dir: Path) -> Path:
    """Get the business unit directory path."""
    return project_dir / "docs" / "业务单元"


def _file_hash(file_path: Path) -> str:
    """MD5 hash of file content."""
    return hashlib.md5(file_path.read_bytes()).hexdigest()


def _get_hash_store(project_dir: Path) -> Path:
    """Get path to the file hash store."""
    napkin_dir = project_dir / ".napkin"
    napkin_dir.mkdir(parents=True, exist_ok=True)
    return napkin_dir / "file_hashes.json"


def _load_hashes(project_dir: Path) -> dict:
    """Load stored file hashes."""
    hash_file = _get_hash_store(project_dir)
    if hash_file.exists():
        return json.loads(hash_file.read_text())
    return {}


def _save_hashes(project_dir: Path, hashes: dict) -> None:
    """Save file hashes to disk."""
    hash_file = _get_hash_store(project_dir)
    hash_file.write_text(json.dumps(hashes, indent=2, ensure_ascii=False))


def _is_git_repo(project_dir: Path) -> bool:
    """Check if project_dir is inside a git repository."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=project_dir, capture_output=True, text=True, timeout=5,
        )
        return result.returncode == 0 and result.stdout.strip() == "true"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def _has_git_head(project_dir: Path) -> bool:
    """Check if git repo has at least one commit."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD"],
            cwd=project_dir, capture_output=True, text=True, timeout=5,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def _is_business_unit(rel_path: str) -> bool:
    """Check if a path is a business unit .md file (not README/_template)."""
    p = Path(rel_path)
    return (
        p.suffix == ".md"
        and p.name not in ("README.md", "_template.md")
        and "业务单元" in str(p)
    )


def _scan_with_git(project_dir: Path) -> List[FileChange]:
    """Use git status --porcelain to detect changes."""
    changes = []

    if not _is_git_repo(project_dir) or not _has_git_head(project_dir):
        return []

    # git status --porcelain gives: "XY path" where X=index, Y=working tree
    #   ?? = untracked, M = modified, D = deleted, A = added
    # core.quotePath=false ensures Chinese paths aren't escaped on Windows
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", "status", "--porcelain", "-u"],
        cwd=project_dir, capture_output=True, text=True, timeout=10,
    )

    for line in result.stdout.strip().split("\n"):
        line = line.strip()
        if not line:
            continue

        status = line[:2]
        # Path starts after 2 status chars + 1 space
        rel_path = line[3:].strip()

        if not _is_business_unit(rel_path):
            continue

        full_path = (project_dir / rel_path).resolve()

        if status == "??":  # Untracked = ADDED
            changes.append(FileChange(
                file_path=full_path,
                change_type=ChangeType.ADDED,
                relative_path=rel_path,
            ))
        elif "M" in status or "A" in status:  # Modified or staged
            changes.append(FileChange(
                file_path=full_path,
                change_type=ChangeType.MODIFIED,
                relative_path=rel_path,
            ))
        elif "D" in status:  # Deleted
            changes.append(FileChange(
                file_path=full_path,
                change_type=ChangeType.DELETED,
                relative_path=rel_path,
            ))

    return changes


def _scan_with_hashes(project_dir: Path, bu_dir: Path) -> List[FileChange]:
    """Use file hash store to detect changes (fallback when no git)."""
    changes = []
    stored = _load_hashes(project_dir)

    current_files = set()
    if bu_dir.exists():
        for md_file in bu_dir.glob("*.md"):
            if md_file.name in ("README.md", "_template.md"):
                continue
            current_files.add(md_file.name)
            current_hash = _file_hash(md_file)
            stored_key = f"业务单元/{md_file.name}"
            rel = str(md_file.relative_to(project_dir))

            if stored_key not in stored:
                changes.append(FileChange(
                    file_path=md_file,
                    change_type=ChangeType.ADDED,
                    relative_path=rel,
                ))
            elif stored[stored_key] != current_hash:
                changes.append(FileChange(
                    file_path=md_file,
                    change_type=ChangeType.MODIFIED,
                    relative_path=rel,
                ))

            stored[stored_key] = current_hash

    # Check for deleted files
    for key in list(stored.keys()):
        if key.startswith("业务单元/"):
            fname = key.replace("业务单元/", "")
            if fname not in current_files:
                changes.append(FileChange(
                    file_path=bu_dir / fname,
                    change_type=ChangeType.DELETED,
                    relative_path=f"docs/业务单元/{fname}",
                ))
                del stored[key]

    _save_hashes(project_dir, stored)
    return changes


def scan_business_units(project_dir: Path) -> List[FileChange]:
    """Scan business unit directory for changes.

    Uses git status when available, falls back to file hash comparison.
    Skips README.md and _template.md.
    """
    bu_dir = get_business_unit_dir(project_dir)

    if not bu_dir.exists():
        return []

    # Try git first
    git_changes = _scan_with_git(project_dir)
    if git_changes:
        return git_changes

    # Fallback: file hashes
    return _scan_with_hashes(project_dir, bu_dir)