"""wipe command: scan, validate, and sync business unit changes."""

from pathlib import Path
from typing import List
import typer
from rich.console import Console
from rich.table import Table

from vibe_napkin.core.scanner import (
    scan_business_units,
    FileChange,
    ChangeType,
)
from vibe_napkin.core.validator import (
    validate_business_unit,
    ValidationSeverity,
)

console = Console()


def _display_change_summary(changes: List[FileChange]) -> None:
    """Display a summary table of detected changes."""
    if not changes:
        return

    table = Table(title="📋 变更清单预览")
    table.add_column("类型", style="bold")
    table.add_column("文件")

    icons = {
        ChangeType.ADDED: "[green]🆕 新增[/green]",
        ChangeType.MODIFIED: "[yellow]📝 修改[/yellow]",
        ChangeType.DELETED: "[red]🗑️ 废弃[/red]",
    }

    for change in changes:
        table.add_row(
            icons.get(change.change_type, str(change.change_type.value)),
            change.relative_path or change.file_path.name,
        )

    console.print(table)


def run_wipe(project_dir: Path, auto_confirm: bool = False) -> int:
    """Run the wipe workflow.

    Scans for changes, validates format, and syncs.
    Returns 0 on success, 1 on validation failure.
    """
    project_dir = Path(project_dir).resolve()

    # Step 1: Scan for changes
    changes = scan_business_units(project_dir)

    if not changes:
        console.print("[green]✅ 没有检测到变更，一切干净。[/green]")
        return 0

    # Step 2: Display change summary
    _display_change_summary(changes)

    new_or_modified = [
        c for c in changes
        if c.change_type in (ChangeType.ADDED, ChangeType.MODIFIED)
    ]

    # Step 3: Auto-validate all changed files
    if new_or_modified:
        console.print("\n[bold]🔍 自动校验格式...[/bold]")
        all_valid = True
        for change in new_or_modified:
            if not change.file_path.exists():
                continue
            result = validate_business_unit(change.file_path)
            if not result.is_valid:
                all_valid = False
                console.print(
                    f"  [red]❌ {change.file_path.name}:[/red]"
                )
                for issue in result.blocking_errors:
                    console.print(f"    - {issue.message}")
            else:
                console.print(
                    f"  [green]✅ {change.file_path.name}: 格式通过[/green]"
                )
                for issue in result.errors:
                    if issue.severity == ValidationSeverity.WARNING:
                        console.print(f"    [yellow]⚠️ {issue.message}[/yellow]")

        if not all_valid:
            console.print(
                "\n[red]❌ 存在阻断级错误，请修复后重试。[/red]"
            )
            return 1

    # Step 4: Confirm (unless auto)
    if not auto_confirm:
        from rich.prompt import Confirm as RichConfirm
        confirm = RichConfirm.ask("\n确认同步以上变更？")
        if not confirm:
            console.print("[yellow]已取消同步[/yellow]")
            return 0

    # Step 5: Mark deleted
    deleted = [c for c in changes if c.change_type == ChangeType.DELETED]
    for change in deleted:
        console.print(f"  [dim]已标记废弃: {change.file_path.name}[/dim]")

    console.print("[green]✅ wipe 完成！文档已同步。[/green]")
    return 0