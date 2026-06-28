"""Template deployment and rendering for vibe-napkin."""

from __future__ import annotations
from pathlib import Path


def render_template(content: str, variables: dict) -> str:
    """Simple template variable substitution. Replaces {{ key }} placeholders."""
    for key, value in variables.items():
        content = content.replace("{{ " + key + " }}", str(value))
        content = content.replace("{{" + key + "}}", str(value))
    return content


def get_template_root() -> Path:
    """Get the path to the built-in templates directory."""
    return Path(__file__).parent.parent / "templates"


def deploy_templates(
    project_dir: Path,
    project_name: str = "",
) -> None:
    """Deploy all template files to the project directory.

    Creates:
    - .napkin/config.toml
    - docs/README.md
    - docs/业务单元/README.md + _template.md
    - docs/约束基线/README.md + _baseline-*.md
    """
    template_root = get_template_root()

    if not template_root.exists():
        raise FileNotFoundError(
            f"Templates directory not found: {template_root}. "
            "Ensure templates are packaged correctly."
        )

    variables = {"project_name": project_name or project_dir.name}

    # Deploy .napkin/config.toml
    napkin_dir = project_dir / ".napkin"
    napkin_dir.mkdir(parents=True, exist_ok=True)

    src_config = template_root / "napkin-config.toml"
    if src_config.exists():
        content = src_config.read_text(encoding="utf-8")
        rendered = render_template(content, variables)
        (napkin_dir / "config.toml").write_text(rendered, encoding="utf-8")

    # Deploy docs/ directory recursively
    src_docs = template_root / "docs"
    if src_docs.exists():
        for item in src_docs.rglob("*"):
            if item.is_file():
                rel_path = item.relative_to(src_docs)
                dest_file = project_dir / "docs" / rel_path
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                content = item.read_text(encoding="utf-8")
                rendered = render_template(content, variables)
                dest_file.write_text(rendered, encoding="utf-8")