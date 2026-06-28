"""init command: scaffold project with templates and config."""

from pathlib import Path
import typer
from vibe_napkin.core.template import deploy_templates
from vibe_napkin.core.config import create_default_config


def run_init(project_dir: Path, project_name: str = "") -> int:
    """Initialize vibe-napkin in a project directory.

    - Creates .napkin/ directory and config.toml
    - Deploys docs/ template structure (业务单元 + 约束基线)
    """
    project_dir = Path(project_dir).resolve()
    project_dir.mkdir(parents=True, exist_ok=True)

    name = project_name or project_dir.name

    # Deploy templates (creates .napkin/config.toml + docs/)
    deploy_templates(project_dir, project_name=name)

    typer.echo(f"⛺ 支桌子完成！vibe-napkin 已初始化：{project_dir}")
    typer.echo("  📁 .napkin/config.toml")
    typer.echo("  📁 docs/README.md")
    typer.echo("  📁 docs/业务单元/")
    typer.echo("  📁 docs/约束基线/")
    typer.echo()
    typer.echo("  下一步：编写业务单元 → vibe-napkin wipe → vibe-napkin tidy")

    return 0