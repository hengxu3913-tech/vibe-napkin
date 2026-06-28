"""Tests for the template module."""

from vibe_napkin.core.template import deploy_templates, render_template, get_template_root


def test_deploy_templates_creates_structure(tmp_project):
    """Deploy templates creates all expected files."""
    deploy_templates(tmp_project, project_name="test-proj")

    expected = [
        tmp_project / ".napkin" / "config.toml",
        tmp_project / ".napkin" / "mcp" / "_config.py",
        tmp_project / ".napkin" / "mcp" / "build_kb.py",
        tmp_project / ".napkin" / "mcp" / "server.py",
        tmp_project / "docs" / "README.md",
        tmp_project / "docs" / "业务单元" / "README.md",
        tmp_project / "docs" / "业务单元" / "_template.md",
        tmp_project / "docs" / "约束基线" / "README.md",
        tmp_project / "docs" / "约束基线" / "_baseline-技术约束.md",
        tmp_project / "docs" / "约束基线" / "_baseline-部署约束.md",
        tmp_project / "docs" / "约束基线" / "_baseline-产品约束.md",
    ]
    for path in expected:
        assert path.exists(), f"Missing: {path}"


def test_render_template_substitutes_vars():
    """Render template replaces {{ var }} placeholders."""
    content = "Hello {{ name }}!"
    result = render_template(content, {"name": "vibe-napkin"})
    assert result == "Hello vibe-napkin!"


def test_render_template_no_placeholder():
    """Render template with no placeholders returns unchanged."""
    content = "Hello world!"
    result = render_template(content, {"name": "vibe"})
    assert result == "Hello world!"


def test_template_has_toml_with_project_name(tmp_project):
    """Config template renders with the correct project name."""
    deploy_templates(tmp_project, project_name="my-awesome-app")
    config_content = (tmp_project / ".napkin" / "config.toml").read_text()
    assert 'name = "my-awesome-app"' in config_content


def test_template_root_exists():
    """Template root directory should exist."""
    root = get_template_root()
    assert root.exists()
    assert (root / "napkin-config.toml").exists()


def test_deploy_templates_idempotent(tmp_project):
    """Running deploy twice is safe (no errors)."""
    deploy_templates(tmp_project, project_name="test")
    deploy_templates(tmp_project, project_name="test")
    assert (tmp_project / "docs" / "README.md").exists()