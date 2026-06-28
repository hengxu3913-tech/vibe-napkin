"""Business unit format validation engine.

Validates that business unit markdown files conform to the 6-section template:
- ## 关键词 (required)
- ## 业务规则 (required)
- ## 代码位置 (optional)
- ## 关联业务单元 (optional)
- ## 历史决策 (optional)
- ## 变更触发器 (optional)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List
import re


class ValidationSeverity(Enum):
    BLOCKING = "blocking"
    WARNING = "warning"


@dataclass
class ValidationIssue:
    severity: ValidationSeverity
    message: str
    section: str = ""


@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[ValidationIssue] = field(default_factory=list)

    @property
    def blocking_errors(self) -> List[ValidationIssue]:
        return [e for e in self.errors if e.severity == ValidationSeverity.BLOCKING]


def _parse_sections(content: str) -> dict[str, str]:
    """Parse markdown sections by ## headings."""
    sections = {}
    parts = re.split(r'^##\s+', content, flags=re.MULTILINE)
    for part in parts[1:]:
        lines = part.strip().split('\n', 1)
        if lines:
            heading = lines[0].strip()
            body = lines[1].strip() if len(lines) > 1 else ""
            sections[heading] = body
    return sections


def _find_invalid_references(content: str, base_dir: Path) -> List[str]:
    """Find markdown link references to .md files that don't exist."""
    refs = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
    bad = []
    for _, path in refs:
        if path.endswith('.md'):
            ref_path = (base_dir / path).resolve()
            if not ref_path.exists():
                bad.append(path)
    return bad


def validate_business_unit(file_path: Path) -> ValidationResult:
    """Validate a business unit markdown file against the 6-section template."""
    result = ValidationResult(is_valid=True)

    if not file_path.exists():
        result.errors.append(ValidationIssue(
            severity=ValidationSeverity.BLOCKING,
            message=f"文件不存在: {file_path}",
        ))
        result.is_valid = False
        return result

    content = file_path.read_text(encoding="utf-8")
    lines = content.split('\n')
    line_count = len(lines)

    # Check line count
    if line_count > 200:
        result.errors.append(ValidationIssue(
            severity=ValidationSeverity.WARNING,
            message=f"行数 {line_count} 超过建议上限 200 行",
        ))

    # Parse sections
    sections = _parse_sections(content)

    # Check required sections
    for required in ["关键词", "业务规则"]:
        if required not in sections:
            result.errors.append(ValidationIssue(
                severity=ValidationSeverity.BLOCKING,
                message=f"缺少必填段: ## {required}",
                section=required,
            ))
            result.is_valid = False
        elif not sections[required].strip():
            result.errors.append(ValidationIssue(
                severity=ValidationSeverity.BLOCKING,
                message=f"## {required} 内容为空",
                section=required,
            ))
            result.is_valid = False

    # Check references
    invalid_refs = _find_invalid_references(content, file_path.parent)
    for ref in invalid_refs:
        result.errors.append(ValidationIssue(
            severity=ValidationSeverity.WARNING,
            message=f"关联业务单元引用不可达: {ref}",
        ))

    return result


def batch_validate(unit_dir: Path) -> dict[str, ValidationResult]:
    """Validate all .md files in a business unit directory.

    Skips README.md and _template.md (they're index/template files).
    """
    results = {}
    if not unit_dir.exists():
        return results
    for md_file in sorted(unit_dir.glob("*.md")):
        if md_file.name in ("README.md", "_template.md"):
            continue
        results[md_file.name] = validate_business_unit(md_file)
    return results