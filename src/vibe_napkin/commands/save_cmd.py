"""save command: create a progress checkpoint."""

from pathlib import Path
from rich.console import Console

from vibe_napkin.models.checkpoint import get_next_checkpoint, save_checkpoint
from vibe_napkin.core.scanner import get_business_unit_dir

console = Console()


def run_save(project_dir: Path, label: str) -> int:
    """Save current progress as a checkpoint."""
    project_dir = Path(project_dir).resolve()

    cp = get_next_checkpoint(project_dir, label)

    # Auto-detect business units
    bu_dir = get_business_unit_dir(project_dir)
    if bu_dir.exists():
        units = sorted(bu_dir.glob("*.md"))
        cp.business_units = [
            u.name for u in units if u.name not in ("README.md", "_template.md")
        ]

    save_checkpoint(project_dir, cp)

    console.print(f"[green]💾 存档成功！[/green]")
    console.print(f"  📍 存档 ID: [bold]{cp.checkpoint_id}[/bold]")
    console.print(f"  🏷️  标签: {cp.label}")
    console.print(f"  📝 业务单元: {len(cp.business_units)} 个")
    if cp.git_commit:
        console.print(f"  🔗 Git: {cp.git_commit}")
    console.print()
    console.print(f"[dim]下次继续: vibe-napkin load {cp.checkpoint_id}[/dim]")

    return 0