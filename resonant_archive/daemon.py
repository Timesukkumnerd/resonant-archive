"""resonant-archive daemon — FastAPI HTTP server.

The daemon's job is to keep the embedding model loaded in memory and
answer search requests from the MCP server over HTTP. It's a separate
process from the MCP server because MCP servers get spawned and killed
repeatedly by clients like Claude Desktop, and we don't want to reload
a 90 MB model on every spawn.

Endpoints:
  GET  /health          -- liveness + current config
  GET  /stats           -- total chunks + per-namespace breakdown
  POST /search          -- semantic search with optional namespace filter

Copyright (C) 2025-2026 Codependent AI
Licensed under the Codependent AI Source-Available License. See LICENSE.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .embed import Embedder
from .store import ArchiveStore


class SearchRequest(BaseModel):
    query: str
    n_results: int = Field(default=5, ge=1, le=50)
    namespace: str | None = None


class SearchHit(BaseModel):
    chunk_id: str
    source_file: str
    text: str
    relevance: float
    namespace: str | None = None
    title: str | None = None
    timestamp: str | None = None
    conversation_id: str | None = None
    provider: str | None = None
    chunk_index: int = 0


class SearchResponse(BaseModel):
    query: str
    namespace: str | None = None
    results: list[SearchHit]
    total: int


class StatsResponse(BaseModel):
    total_chunks: int
    namespaces: dict[str, int]
    data_dir: str
    model: str | None = None


def create_app(data_dir: Path) -> FastAPI:
    """Build a FastAPI app wired to a specific archive directory.

    State (embedder + store) is lazy-loaded in the lifespan hook and kept
    on ``app.state`` for the lifetime of the process.
    """

    @asynccontextmanager
    async def lifespan(fastapi_app: FastAPI) -> AsyncIterator[None]:
        print("[resonant-archive] daemon starting")
        print(f"[resonant-archive] data_dir: {data_dir}")
        print("[resonant-archive] loading embedding model...")
        fastapi_app.state.embedder = Embedder()
        # Touch the model once to force eager load instead of first-query lag.
        _ = fastapi_app.state.embedder.embed(["warmup"])
        fastapi_app.state.store = ArchiveStore(data_dir=data_dir)
        fastapi_app.state.data_dir = data_dir
        print(
            f"[resonant-archive] ready. model: "
            f"{fastapi_app.state.embedder.model_name}"
        )
        try:
            yield
        finally:
            # Chroma keeps file handles until process exit; nothing to release.
            pass

    app = FastAPI(title="resonant-archive daemon", lifespan=lifespan)

    @app.get("/health")
    async def health() -> dict[str, Any]:
        embedder: Embedder | None = getattr(app.state, "embedder", None)
        return {
            "status": "ok",
            "data_dir": str(data_dir),
            "model": embedder.model_name if embedder is not None else None,
        }

    @app.get("/stats", response_model=StatsResponse)
    async def stats() -> StatsResponse:
        try:
            store: ArchiveStore = app.state.store
            embedder: Embedder = app.state.embedder
            return StatsResponse(
                total_chunks=store.count(),
                namespaces=store.list_namespaces(),
                data_dir=str(data_dir),
                model=embedder.model_name,
            )
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.post("/search", response_model=SearchResponse)
    async def search(request: SearchRequest) -> SearchResponse:
        try:
            store: ArchiveStore = app.state.store
            embedder: Embedder = app.state.embedder
            hits = store.search(
                query=request.query,
                embedder=embedder,
                n_results=request.n_results,
                namespace=request.namespace,
            )
            return SearchResponse(
                query=request.query,
                namespace=request.namespace,
                results=[
                    SearchHit(
                        chunk_id=h.chunk_id,
                        source_file=h.source_file,
                        text=h.text,
                        relevance=h.relevance,
                        namespace=h.namespace,
                        title=h.title,
                        timestamp=h.timestamp,
                        conversation_id=h.conversation_id,
                        provider=h.provider,
                        chunk_index=h.chunk_index,
                    )
                    for h in hits
                ],
                total=len(hits),
            )
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    return app


def run_daemon(data_dir: Path, port: int = 8766) -> None:
    """Run the daemon via uvicorn. Blocks until interrupted (Ctrl+C)."""
    app = create_app(data_dir)
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
