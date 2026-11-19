from __future__ import annotations

import json
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator

from backend.settings import PROJECT_ROOT


class MCPToolClient:
    """Small stdio MCP client for the project's fixed structured-data tools."""

    def __init__(self) -> None:
        self._session: Any = None

    @asynccontextmanager
    async def connected(self) -> AsyncIterator["MCPToolClient"]:
        try:
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client
        except ImportError as exc:
            raise RuntimeError("Install requirements.txt to connect to the MCP server.") from exc

        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "backend.mcp_server"],
            cwd=str(Path(PROJECT_ROOT)),
        )
        async with stdio_client(params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                self._session = session
                try:
                    yield self
                finally:
                    self._session = None

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        if self._session is None:
            raise RuntimeError("Connect to the MCP server before calling a tool.")
        if name not in {"get_product_details", "check_order_status", "place_order"}:
            raise ValueError(f"Unsupported store operation: {name}")
        result = await self._session.call_tool(name, arguments)
        if getattr(result, "isError", False):
            error_text = "\n".join(
                item.text for item in getattr(result, "content", []) if hasattr(item, "text")
            )
            raise RuntimeError(f"MCP tool {name} failed: {error_text}")
        structured = getattr(result, "structuredContent", None)
        if structured is not None:
            return structured
        text = "\n".join(
            item.text for item in getattr(result, "content", []) if hasattr(item, "text")
        )
        if not text:
            return {}
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"result": text}
