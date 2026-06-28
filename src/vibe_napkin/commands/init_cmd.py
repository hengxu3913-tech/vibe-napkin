"""init command: scaffold project with templates and config."""

from pathlib import Path
import subprocess
import sys
import typer
from vibe_napkin.core.template import deploy_templates


def run_init(project_dir: Path, project_name: str = "") -> int:
    """Initialize vibe-napkin in a project directory.

    - Creates .napkin/ directory and config.toml
    - Deploys docs/ template structure (业务单元 + 约束基线)
    - Deploys mcp/ MCP server templates
    - Installs zvec + MCP dependencies
    """
    project_dir = Path(project_dir).resolve()
    project_dir.mkdir(parents=True, exist_ok=True)

    name = project_name or project_dir.name

    # Deploy templates (creates .napkin/config.toml + docs/ + mcp/)
    deploy_templates(project_dir, project_name=name)

    typer.echo(f"⛺ 支桌子完成！vibe-napkin 已初始化：{project_dir}")
    typer.echo("  📁 .napkin/config.toml")
    typer.echo("  📁 .napkin/mcp/            ← MCP 知识库服务")
    typer.echo("  📁 docs/README.md")
    typer.echo("  📁 docs/业务单元/")
    typer.echo("  📁 docs/约束基线/")

    # Install dependencies
    typer.echo()
    typer.echo("📦 安装 zvec + MCP 依赖...")
    deps = [
        "zvec @ git+https://github.com/alibaba/zvec.git",
        "mcp>=1.0.0",
        "openai>=1.50.0",
        "python-dotenv>=1.0.0",
        "tomlkit>=0.12.0",
    ]
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install"] + deps,
            capture_output=True, text=True, timeout=120,
        )
        typer.echo("  ✅ zvec 及依赖安装完成")
    except subprocess.TimeoutExpired:
        typer.echo("  ⚠️  依赖安装超时，请手动执行：")
        typer.echo(f"     pip install {' '.join(deps)}")
    except Exception as e:
        typer.echo(f"  ⚠️  依赖安装出错（{e}），请手动安装：")
        typer.echo(f"     pip install {' '.join(deps)}")

    typer.echo()
    typer.echo("  下一步：")
    typer.echo("  1. 编辑 .napkin/config.toml，填入你的 Embedding API Key")
    typer.echo("  2. 编写业务单元文档 → vibe-napkin wipe")
    typer.echo(f"  3. python .napkin/mcp/build_kb.py  # 首次建库")
    typer.echo("  4. vibe-napkin tidy                 # 更新知识库")

    return 0