"""Tests for the validator module."""

from pathlib import Path
from vibe_napkin.core.validator import (
    validate_business_unit,
    ValidationSeverity,
    batch_validate,
)


def test_valid_business_unit_passes(tmp_project):
    """A properly formed 6-section business unit passes validation."""
    content = """# 商品采集

## 关键词
商品,采集,ozon

## 业务规则
- 通过 Playwright 打开商品链接采集数据

## 代码位置
- crawl_product: `src/crawler.py::crawl_product` 42

## 关联业务单元
- [数据映射](./数据映射.md)

## 历史决策（近 3 次）
- 2026-06-01（abc123）：决定用 Playwright 而非 API

## 变更触发器
- OZON 页面 DOM 结构变更
"""
    file_path = tmp_project / "docs" / "业务单元" / "test-unit.md"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content)

    result = validate_business_unit(file_path)
    assert result.is_valid is True
    assert len(result.blocking_errors) == 0


def test_missing_keywords_is_blocking(tmp_project):
    """Missing ## 关键词 section blocks validation."""
    content = """# 商品采集

## 业务规则
- 规则内容
"""
    file_path = tmp_project / "test-unit.md"
    file_path.write_text(content)

    result = validate_business_unit(file_path)
    assert result.is_valid is False
    assert any(e.severity == ValidationSeverity.BLOCKING for e in result.errors)


def test_excessive_lines_issues_warning(tmp_project):
    """Over 200 lines triggers a warning (not blocking)."""
    lines = ["# Title\n"] + ["## 关键词\n"] + ["key, words\n"] + ["## 业务规则\n"] + ["- rule\n"] + ["\n"] * 200
    content = "".join(lines)
    file_path = tmp_project / "test-unit.md"
    file_path.write_text(content)

    result = validate_business_unit(file_path)
    assert result.is_valid is True  # Warning doesn't block
    assert any(e.severity == ValidationSeverity.WARNING for e in result.errors)


def test_empty_required_section_is_blocking(tmp_project):
    """Required section with empty content is blocking."""
    content = """# Test

## 关键词

## 业务规则
- Some rule
"""
    file_path = tmp_project / "test-unit.md"
    file_path.write_text(content)

    result = validate_business_unit(file_path)
    assert result.is_valid is False


def test_non_existent_file_is_blocking(tmp_project):
    """Validating a non-existent file returns blocking error."""
    result = validate_business_unit(tmp_project / "nope.md")
    assert result.is_valid is False


def test_broken_reference_issues_warning(tmp_project):
    """Reference to non-existent file warns."""
    content = """# 商品采集

## 关键词
key

## 业务规则
- rule

## 代码位置
- func: `path::func` 1

## 关联业务单元
- [不存在的单元](./不存在的单元.md)

## 历史决策（近 3 次）
- 2026-01-01（a）：init

## 变更触发器
- trigger
"""
    file_path = tmp_project / "test-unit.md"
    file_path.write_text(content)

    result = validate_business_unit(file_path)
    assert result.is_valid is True
    warning_issues = [e for e in result.errors if e.severity == ValidationSeverity.WARNING]
    assert any("引用" in e.message for e in warning_issues)


def test_batch_validate_skips_readme(tmp_project):
    """batch_validate skips README.md and _template.md files."""
    bu_dir = tmp_project / "docs" / "业务单元"
    bu_dir.mkdir(parents=True, exist_ok=True)

    (bu_dir / "README.md").write_text("# README")
    (bu_dir / "_template.md").write_text("# Template")
    (bu_dir / "001-real-unit.md").write_text("""# Real

## 关键词
a

## 业务规则
- b
""")

    results = batch_validate(bu_dir)
    assert "README.md" not in results
    assert "_template.md" not in results
    assert "001-real-unit.md" in results
    assert results["001-real-unit.md"].is_valid