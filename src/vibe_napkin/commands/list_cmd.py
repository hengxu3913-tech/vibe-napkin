"""list command: show all checkpoints."""

from pathlib import Path
from rich.console import Console
from rich.table import Table

from vibe_napkin.models.checkpoint import list_checkpoints

console = Console()


def run_list(project_dir: Path) -> int:
    """List all saved checkpoints."""
    project_dir = Path(project_dir).resolve()

    checkpoints = list_checkpoints(project_dir)

    if not checkpoints:
        console.print("[yellow]📋 暂无存档[/yellow]")
        console.print(
            "开发完一个功能后，使用 "
            "[bold]vibe-napkin save -l '你的标签'[/bold] 创建存档"
        )
        return 0

    table = Table(title="💾 存档清单")
    table.add_column("存档 ID")
    table.add_column("标签")
    table.add_column("时间")
    table.add_column("业务单元")
    table.add_column("Git")

    for cp in checkpoints:
        table.add_row(
            cp.checkpoint_id,
            cp.label,
            cp.created_at[:10] if cp.created_at else "-",
            str(len(cp.business_units)),
            cp.git_commit[:8] if cp.git_commit else "-",
        )

    console.print(table)
    console.print(f"\n[dim]共 {len(checkpoints)} 个存档[/dim]")

    return 0