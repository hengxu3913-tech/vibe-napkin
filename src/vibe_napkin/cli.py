"""vibe-napkin CLI entry point."""

import typer
from pathlib import Path
from typing import Optional

from vibe_napkin.commands.init_cmd import run_init
from vibe_napkin.commands.wipe_cmd import run_wipe
from vibe_napkin.commands.tidy_cmd import run_tidy

app = typer.Typer(
    name="vibe-napkin",
    help="🧻 You mouth the code, we wipe the crumbs.",
    no_args_is_help=True,
)


@app.command()
def init(
    project_dir: Path = typer.Argument(
        ".", help="Project directory to initialize"
    ),
    project_name: Optional[str] = typer.Option(
        None, "--name", "-n", help="Project name (defaults to directory name)"
    ),
):
    """⛺ Initialize vibe-napkin in a project (env + templates)."""
    name = project_name or (project_dir.name if project_dir.name != "." else "project")
    exit_code = run_init(project_dir, project_name=name)
    raise typer.Exit(code=exit_code)


@app.command()
def wipe(
    project_dir: Path = typer.Option(
        ".", "--dir", "-d", help="Project directory"
    ),
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Auto-confirm without prompt"
    ),
):
    """🧻 Scan and sync business unit changes."""
    exit_code = run_wipe(project_dir, auto_confirm=yes)
    raise typer.Exit(code=exit_code)


@app.command()
def tidy(
    project_dir: Path = typer.Option(
        ".", "--dir", "-d", help="Project directory"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Preview only, no actual sync"
    ),
    force: bool = typer.Option(
        False, "--force", help="Skip MCP lock detection"
    ),
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Auto-confirm without prompt"
    ),
):
    """🗑️ Sync business units to vector knowledge base."""
    exit_code = run_tidy(project_dir, dry_run=dry_run, force=force, auto_confirm=yes)
    raise typer.Exit(code=exit_code)


@app.command()
def save(
    project_dir: Path = typer.Option(
        ".", "--dir", "-d", help="Project directory"
    ),
    label: str = typer.Option(
        ..., "--label", "-l", help="Checkpoint label (e.g. '商品采集完成')"
    ),
):
    """💾 Save current progress as a checkpoint."""
    typer.echo("💾 save: Not yet implemented")


@app.command()
def load(
    project_dir: Path = typer.Option(
        ".", "--dir", "-d", help="Project directory"
    ),
    checkpoint_id: str = typer.Argument(
        ..., help="Checkpoint ID (date-serial-label or index number)"
    ),
):
    """📂 Restore a checkpoint to continue progress."""
    typer.echo("📂 load: Not yet implemented")


@app.command()
def list(
    project_dir: Path = typer.Option(
        ".", "--dir", "-d", help="Project directory"
    ),
):
    """📋 List all checkpoints."""
    typer.echo("📋 list: Not yet implemented")