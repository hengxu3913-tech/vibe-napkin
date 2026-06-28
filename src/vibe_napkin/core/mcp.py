"""MCP status detection and lock management for vibe-napkin."""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import socket
import time

from vibe_napkin.core.config import NapkinConfig


class McpStatus(Enum):
    FREE = "free"
    BUSY = "busy"
    UNKNOWN = "unknown"


@dataclass
class McpStatusResult:
    status: McpStatus
    message: str = ""


def _check_port(host: str, port: int) -> bool:
    """Check if a TCP port is open."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


def check_mcp_status(config: NapkinConfig) -> McpStatusResult:
    """Check if MCP knowledge base is currently active.

    Returns FREE if MCP is not running (safe to sync).
    Returns BUSY if MCP is running and may be in use.
    """
    if not config.mcp_enabled:
        return McpStatusResult(McpStatus.FREE, "MCP 未启用")

    port_open = _check_port("127.0.0.1", config.mcp_port)

    if port_open:
        return McpStatusResult(
            McpStatus.BUSY,
            f"MCP 知识库正在运行（127.0.0.1:{config.mcp_port}）"
        )
    else:
        return McpStatusResult(
            McpStatus.FREE,
            "MCP 知识库未运行，可以安全同步"
        )


def wait_for_mcp_free(
    config: NapkinConfig,
    timeout: int = 30,
    interval: int = 2,
) -> bool:
    """Wait for MCP to become free. Returns True if freed, False if timeout."""
    start = time.time()
    while time.time() - start < timeout:
        result = check_mcp_status(config)
        if result.status == McpStatus.FREE:
            return True
        time.sleep(interval)
    return False