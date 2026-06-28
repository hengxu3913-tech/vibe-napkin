"""Tests for the MCP module."""

from vibe_napkin.core.config import NapkinConfig
from vibe_napkin.core.mcp import check_mcp_status, McpStatus


def test_check_mcp_status_no_server(tmp_project):
    """When MCP is not running on port, status is FREE."""
    config = NapkinConfig(mcp_enabled=True, mcp_port=19999, project_name="test")
    result = check_mcp_status(config)
    assert result.status == McpStatus.FREE


def test_check_mcp_status_disabled(tmp_project):
    """When MCP is disabled, status is FREE."""
    config = NapkinConfig(mcp_enabled=False, project_name="test")
    result = check_mcp_status(config)
    assert result.status == McpStatus.FREE