"""Business unit data model."""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class BusinessUnit:
    """A single business unit document.

    Each business unit is a markdown file (≤200 lines) that vertically
    covers product, tech, deployment, and database for one feature.
    """

    name: str
    file_path: Path
    line_count: int = 0
    sections: dict[str, str] = field(default_factory=dict)

    REQUIRED_SECTIONS = ["关键词", "业务规则"]
    OPTIONAL_SECTIONS = ["代码位置", "关联业务单元", "历史决策", "变更触发器"]
    MAX_LINES = 200

    @property
    def is_complete(self) -> bool:
        """Check if all required sections are present."""
        return all(s in self.sections for s in self.REQUIRED_SECTIONS)