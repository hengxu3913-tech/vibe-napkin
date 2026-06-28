"""Checkpoint data model for save/load functionality.

Checkpoints are game-save-style snapshots of project progress,
stored as JSON in .napkin/checkpoints/YYYY-MM-DD-NNN-label.json.
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import json
import re
import subprocess


@dataclass
class Checkpoint:
    """A project progress checkpoint."""

    checkpoint_id: str
    label: str
    created_at: str = ""
    git_commit: str = ""
    business_units: List[str] = field(default_factory=list)
    zvec_index_version: str = ""
    todo: str = ""
    milestone: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


def get_checkpoints_dir(project_dir: Path) -> Path:
    """Get the checkpoints directory, creating it if needed."""
    ckpt_dir = project_dir / ".napkin" / "checkpoints"
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    return ckpt_dir


def get_checkpoint_path(project_dir: Path, checkpoint_id: str) -> Path:
    """Get the file path for a checkpoint ID."""
    return get_checkpoints_dir(project_dir) / f"{checkpoint_id}.json"


def _get_git_commit(project_dir: Path) -> str:
    """Get the current short git commit hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=project_dir, capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return ""


def get_next_checkpoint(project_dir: Path, label: str) -> Checkpoint:
    """Create a new Checkpoint with auto-generated ID.

    ID format: YYYY-MM-DD-NNN-label
    NNN auto-increments based on existing checkpoints today.
    """
    ckpt_dir = get_checkpoints_dir(project_dir)
    today = datetime.now().strftime("%Y-%m-%d")

    # Find max serial number for today
    max_serial = 0
    for f in ckpt_dir.glob(f"{today}-*.json"):
        match = re.match(rf"{re.escape(today)}-(\d{{3}})-", f.stem)
        if match:
            serial = int(match.group(1))
            max_serial = max(max_serial, serial)

    serial = max_serial + 1
    safe_label = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fff_-]', '-', label)[:40]
    cid = f"{today}-{serial:03d}-{safe_label}"

    git_commit = _get_git_commit(project_dir)

    return Checkpoint(
        checkpoint_id=cid,
        label=label,
        git_commit=git_commit,
    )


def save_checkpoint(project_dir: Path, checkpoint: Checkpoint) -> None:
    """Save a checkpoint to disk as JSON."""
    ckpt_path = get_checkpoint_path(project_dir, checkpoint.checkpoint_id)
    ckpt_path.parent.mkdir(parents=True, exist_ok=True)
    with open(ckpt_path, "w", encoding="utf-8") as f:
        json.dump(asdict(checkpoint), f, indent=2, ensure_ascii=False)


def load_checkpoint(
    project_dir: Path, checkpoint_id: str
) -> Optional[Checkpoint]:
    """Load a checkpoint by ID. Returns None if not found."""
    ckpt_path = get_checkpoint_path(project_dir, checkpoint_id)
    if not ckpt_path.exists():
        return None
    with open(ckpt_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return Checkpoint(**data)


def list_checkpoints(project_dir: Path) -> List[Checkpoint]:
    """List all checkpoints sorted by ID (chronological)."""
    ckpt_dir = get_checkpoints_dir(project_dir)
    checkpoints = []
    for json_file in sorted(ckpt_dir.glob("*.json")):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            checkpoints.append(Checkpoint(**data))
        except (json.JSONDecodeError, KeyError):
            continue
    return checkpoints