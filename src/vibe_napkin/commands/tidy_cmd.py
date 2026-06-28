"""tidy command: sync business units to vector knowledge base with deadlock protection."""

from pathlib import Path
import typer
from rich.console import Console

from vibe_napkin.core.config import load_config
from vibe_napkin.core.mcp import check_mcp_status, McpStatus
from vibe_napkin.core.zvec_bridge import sync_to_zvec, check_zvec_available

console = Console()


def run_tidy(
    project_dir: Path,
    dry_run: bool = False,
    force: bool = False,
    auto_confirm: bool = False,
) -> int:
    """Run the tidy workflow with deadlock protocol.

    1. Check zvec availability
    2. MCP lock detection (unless --force)
    3. Confirm sync
    4. Sync to zvec
    5. Self-check and notify

    Returns 0 on success, 1 on failure.
    """
    project_dir = Path(project_dir).resolve()
    config = load_config(project_dir)

    # Step 1: Check zvec availability
    if not check_zvec_available():
        console.print("[red]❌ zvec 未安装，无法同步知识库[/red]")
        console.print("   请先安装: [yellow]pip install zvec[/yellow]")
        return 1

    # Step 2: MCP lock detection (unless --force)
    if not force:
        mcp_status = check_mcp_status(config)

        if mcp_status.status == McpStatus.BUSY:
            console.print(
                "[yellow]⚠️  检测到 MCP 知识库正在被 AI 引用中[/yellow]"
            )
            console.print(f"  {mcp_status.message}")
            console.print()
            console.print(
                "[bold]请关闭 AI 侧的 MCP 知识库连接后再继续。[/bold]"
            )

            if not auto_confirm:
                from rich.prompt import Confirm as RichConfirm
                confirmed = RichConfirm.ask("是否已关闭 MCP 连接？")
                if not confirmed:
                    console.print("[yellow]已取消同步[/yellow]")
                    return 0
            else:
                console.print("[dim]--yes 模式，假定 MCP 已释放[/dim]")

    # Step 3: Preview or confirm
    if dry_run:
        console.print("[yellow]🔍 --dry-run 模式：预览同步内容[/yellow]")

    if not auto_confirm and not dry_run:
        from rich.prompt import Confirm as RichConfirm
        confirmed = RichConfirm.ask("\n确认同步知识库？")
        if not confirmed:
            console.print("[yellow]已取消同步[/yellow]")
            return 0

    # Step 4: Sync to zvec
    console.print("\n[bold]🗑️  正在收拾桌子，同步知识库...[/bold]")
    success = sync_to_zvec(project_dir, dry_run=dry_run)

    if not success:
        console.print("[red]❌ tidy 失败，请检查 zvec 配置[/red]")
        return 1

    # Step 5: Self-check and notify
    if not dry_run:
        console.print()
        console.print("[green]✅ 🗑️  桌子收拾好了！[/green]")
        console.print()
        console.print("[bold]请重新连接 MCP 知识库，AI 可以继续编码了 🚀[/bold]")

    return 0