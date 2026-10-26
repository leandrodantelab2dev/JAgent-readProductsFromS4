"""MCP tool loading indirection layer.

This module is the owned abstraction over get_mcp_tools so tests can patch
`mcp_tools.get_mcp_tools` without touching the provider implementation.
"""
from mcp_providers.agw import get_mcp_tools

__all__ = ["get_mcp_tools"]
