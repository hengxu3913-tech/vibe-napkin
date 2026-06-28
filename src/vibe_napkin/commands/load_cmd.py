"""load command: restore a checkpoint context."""

from pathlib import Path
from rich.console import Console

from vibe_napkin.models.checkpoint import load_checkpoint

console = Console()


def run_load(project_dir: Path, checkpoint_id: str) -> int:
    """Load a checkpoint and display its context."""
    project_dir = Path(project_dir).resolve()

    cp = load_checkpoint(project_dir, checkpoint_id)
    if cp is None:
        console.print(f"[red]❌ 存档未找到: {checkpoint_id}[/red]")
        return 1

    console.print(f"[bold]📂 读档: {cp.checkpoint_id}[/bold]")
    console.print(f"  🏷️  标签: {cp.label}")
    console.print(f"  📅 时间: {cp.created_at[:16] if cp.created_at else '-'}")
    if cp.git_commit:
        console.print(f"  🔗 Git: {cp.git_commit}")
    console.print()

    if cp.milestone:
        console.print(f"[bold]🎯 里程碑:[/bold] {cp.milestone}")

    if cp.todo:
        console.print(f"[bold]📋 下一关:[/bold] {cp.todo}")

    if cp.business_units:
        console.print(f"\n[bold]📝 业务单元 ({len(cp.business_units)} 个):[/bold]")
        for unit in cp.business_units:
            console.print(f"  - {unit}")

    console.print()
    console.print("[green]✅ 读档完成，继续编码吧 🚀[/green]")

    return 0