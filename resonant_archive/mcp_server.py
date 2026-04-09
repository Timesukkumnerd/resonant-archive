"""resonant-archive MCP server — stdio MCP that forwards to the daemon.

This module implements a Model Context Protocol (MCP) server exposing
two tools to any MCP-compatible AI client (Claude Desktop, Claude Code,
etc.):

  - ``archive_search(query, namespace?, n_results?)``
  - ``archive_stats()``

Both tools forward to the HTTP daemon (``resonant-archive serve``). The
split lets the embedding model stay warm in the daemon while the MCP
process is spawned fresh by the client on each session.

Copyright (C) 2025-2026 Codependent AI
Licensed under the Codependent AI Source-Available License. See LICENSE.
"""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

DEFAULT_DAEMON_URL = "http://localhost:8766"


# ---------------------------------------------------------------------------
# Formatters — turn JSON responses into human-readable text blocks
# ---------------------------------------------------------------------------


def _format_search(data: dict[str, Any]) -> str:
    results = data.get("results") or []
    query = data.get("query", "")
    namespace = data.get("namespace")
    total = data.get("total", 0)

    header = f"Search: {query!r}"
    if namespace:
        header += f"  (namespace: {namespace})"
    header += f"\nResults: {total}"

    if not results:
        return header + "\n\n(no results)"

    parts = [header, ""]
    for i, r in enumerate(results, 1):
        parts.append("=" * 72)
        ns = r.get("namespace") or "-"
        parts.append(
            f"[{i}] relevance={r.get('relevance', 0):.2f}   namespace={ns}"
        )
        if r.get("title"):
            parts.append(f"    title:     {r['title']}")
        if r.get("timestamp"):
            parts.append(f"    timestamp: {r['timestamp']}")
        if r.get("provider"):
            parts.append(f"    provider:  {r['provider']}")
        if r.get("conversation_id"):
            parts.append(f"    conv_id:   {r['conversation_id']}")
        parts.append(f"    source:    {r.get('source_file', 'unknown')}")
        parts.append("")
        parts.append(r.get("text", ""))
        parts.append("")
    return "\n".join(parts)


def _format_stats(data: dict[str, Any]) -> str:
    total = data.get("total_chunks", 0)
    namespaces = data.get("namespaces") or {}
    model = data.get("model", "unknown")
    data_dir = data.get("data_dir", "unknown")

    lines = [
        f"Archive: {total:,} chunks total",
        f"Model:   {model}",
        f"Dir:     {data_dir}",
    ]
    if namespaces:
        lines.append("")
        lines.append("Namespaces:")
        for ns, count in sorted(namespaces.items(), key=lambda x: -x[1]):
            lines.append(f"  {ns}: {count:,}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# MCP server construction
# ---------------------------------------------------------------------------


def create_server(daemon_url: str = DEFAULT_DAEMON_URL) -> Server:
    server: Server = Server("resonant-archive")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="archive_search",
                description=(
                    "Search a local archive of conversations, notes, or any "
                    "text corpus using semantic similarity. Results include "
                    "provenance metadata (namespace, source file, timestamp, "
                    "conversation_id, title, provider) so you can ground "
                    "responses in the origin of each match. Use this when "
                    "asked about past conversations, when verifying "
                    "continuity across time, for pattern recognition across "
                    "history, or when the current context is missing "
                    "information that may exist in the archive."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": (
                                "What you're looking for, described "
                                "conceptually. Semantic search finds meaning, "
                                "not exact keywords."
                            ),
                        },
                        "namespace": {
                            "type": "string",
                            "description": (
                                "Optional. Restrict the search to a single "
                                "namespace (e.g. 'chatgpt-2024', 'journals'). "
                                "Omit to search across all namespaces."
                            ),
                        },
                        "n_results": {
                            "type": "integer",
                            "description": (
                                "Number of results to return "
                                "(1-20, default 5)."
                            ),
                            "default": 5,
                            "minimum": 1,
                            "maximum": 20,
                        },
                    },
                    "required": ["query"],
                },
            ),
            Tool(
                name="archive_stats",
                description=(
                    "Get statistics about the indexed archive: total chunks, "
                    "per-namespace breakdown, embedding model in use, and "
                    "data directory. Useful for confirming the archive is "
                    "available and seeing what corpora are indexed."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(
        name: str, arguments: dict[str, Any]
    ) -> list[TextContent]:
        if name == "archive_search":
            return await _do_search(daemon_url, arguments)
        if name == "archive_stats":
            return await _do_stats(daemon_url)
        raise ValueError(f"Unknown tool: {name}")

    return server


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------


async def _do_search(
    daemon_url: str, arguments: dict[str, Any]
) -> list[TextContent]:
    query = arguments.get("query")
    if not query:
        return [
            TextContent(
                type="text",
                text="Error: 'query' parameter is required.",
            )
        ]

    payload: dict[str, Any] = {
        "query": query,
        "n_results": arguments.get("n_results", 5),
    }
    ns = arguments.get("namespace")
    if ns:
        payload["namespace"] = ns

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{daemon_url}/search", json=payload, timeout=30.0
            )
            resp.raise_for_status()
            return [
                TextContent(type="text", text=_format_search(resp.json()))
            ]
    except httpx.ConnectError:
        return [
            TextContent(
                type="text",
                text=_daemon_unreachable_message(daemon_url),
            )
        ]
    except Exception as exc:  # noqa: BLE001
        return [
            TextContent(type="text", text=f"Error searching archive: {exc}")
        ]


async def _do_stats(daemon_url: str) -> list[TextContent]:
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{daemon_url}/stats", timeout=10.0)
            resp.raise_for_status()
            return [
                TextContent(type="text", text=_format_stats(resp.json()))
            ]
    except httpx.ConnectError:
        return [
            TextContent(
                type="text",
                text=_daemon_unreachable_message(daemon_url),
            )
        ]
    except Exception as exc:  # noqa: BLE001
        return [TextContent(type="text", text=f"Error getting stats: {exc}")]


def _daemon_unreachable_message(daemon_url: str) -> str:
    return (
        f"Error: cannot reach the resonant-archive daemon at {daemon_url}.\n"
        "Start it in a terminal with:\n"
        "\n"
        "    resonant-archive serve\n"
        "\n"
        "Leave that terminal open while using Claude Desktop or any other "
        "MCP client."
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def run_mcp(daemon_url: str = DEFAULT_DAEMON_URL) -> None:
    """Run the MCP stdio server. Blocks until the client disconnects."""
    asyncio.run(_run(daemon_url))


async def _run(daemon_url: str) -> None:
    server = create_server(daemon_url)
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )
