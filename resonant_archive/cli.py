"""resonant-archive CLI — typer-based command surface.

Commands:
  import      Chunk and embed a directory of text files into the archive.
  search      Semantic search from the command line.
  stats       Show archive statistics.
  serve       Start the HTTP daemon (keeps the embedding model loaded).
  mcp         Run the MCP stdio server (wired to the daemon).

All commands default to the archive stored at ~/.resonant-archive/ and
can be redirected with the --data-dir flag.

Copyright (C) 2025-2026 Codependent AI
Licensed under the Codependent AI Source-Available License. See LICENSE.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table

from . import __version__
from .chunker import chunk_directory
from .embed import Embedder
from .store import ArchiveStore

app = typer.Typer(
    name="resonant-archive",
    help=(
        "Local-first retrieval for AI conversation archives and arbitrary "
        "text corpora. Part of the Resonant ecosystem."
    ),
    add_completion=False,
    no_args_is_help=True,
)
console = Console()


def _default_data_dir() -> Path:
    return Path.home() / ".resonant-archive"


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"resonant-archive {__version__}")
        raise typer.Exit()


@app.callback()
def root(
    version: Optional[bool] = typer.Option(  # noqa: B008
        None,
        "--version",
        "-V",
        callback=_version_callback,
        is_eager=True,
        help="Show the version and exit.",
    ),
) -> None:
    """Global options. See the commands below for what the tool does."""


# ---------------------------------------------------------------------------
# import
# ---------------------------------------------------------------------------


@app.command("import")
def cmd_import(
    directory: Path = typer.Argument(  # noqa: B008
        ...,
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
        help="Directory containing .md / .txt files to index.",
    ),
    namespace: Optional[str] = typer.Option(  # noqa: B008
        None,
        "--namespace",
        "-n",
        help="Namespace tag for this corpus. Defaults to the directory name.",
    ),
    data_dir: Path = typer.Option(  # noqa: B008
        _default_data_dir(),
        "--data-dir",
        help="Where the archive index lives.",
    ),
    strategy: str = typer.Option(  # noqa: B008
        "paragraph",
        "--strategy",
        help="Chunking strategy: 'paragraph' (default) or 'window'.",
    ),
) -> None:
    """Chunk and embed a directory of text files into the archive."""
    ns = namespace or directory.name
    console.print(
        f"[bold]Importing[/bold] [cyan]{directory}[/cyan] "
        f"into namespace [magenta]{ns}[/magenta]"
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("{task.description}"),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("Walking and chunking files", total=None)
        chunks = chunk_directory(directory, strategy=strategy)
        progress.update(task, description=f"Chunked {len(chunks)} pieces")

    if not chunks:
        console.print("[yellow]No text files found. Nothing to index.[/yellow]")
        raise typer.Exit(code=1)

    console.print(
        f"Chunked [bold]{len(chunks):,}[/bold] pieces. "
        "Loading embedding model (first run downloads ~90 MB)..."
    )
    embedder = Embedder()
    store = ArchiveStore(data_dir=data_dir)

    batch_size = 64
    with Progress(
        SpinnerColumn(),
        TextColumn("{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Embedding + storing", total=len(chunks))
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            store.add_chunks(
                batch,
                namespace=ns,
                embedder=embedder,
                batch_size=len(batch),
            )
            progress.update(task, advance=len(batch))

    total = store.count()
    ns_count = store.count(namespace=ns)
    console.print()
    console.print(
        f"[green][OK][/green] Imported [bold]{ns_count:,}[/bold] chunks "
        f"into namespace [magenta]{ns}[/magenta]"
    )
    console.print(f"      Total chunks in archive: [bold]{total:,}[/bold]")
    console.print(f"      Archive location: [cyan]{data_dir}[/cyan]")


# ---------------------------------------------------------------------------
# search
# ---------------------------------------------------------------------------


@app.command("search")
def cmd_search(
    query: str = typer.Argument(..., help="Search query."),  # noqa: B008
    namespace: Optional[str] = typer.Option(  # noqa: B008
        None,
        "--namespace",
        "-n",
        help="Limit results to a single namespace.",
    ),
    n: int = typer.Option(  # noqa: B008
        5, "--n-results", "-c", help="Number of results to return."
    ),
    data_dir: Path = typer.Option(  # noqa: B008
        _default_data_dir(),
        "--data-dir",
        help="Archive index location.",
    ),
) -> None:
    """Search the archive semantically from the command line."""
    if not data_dir.exists():
        console.print(f"[red]No archive found at {data_dir}[/red]")
        console.print("Run [cyan]resonant-archive import <dir>[/cyan] first.")
        raise typer.Exit(code=1)

    with console.status("Loading embedding model...", spinner="dots"):
        embedder = Embedder()
        store = ArchiveStore(data_dir=data_dir)

    with console.status(f"Searching for: {query}", spinner="dots"):
        results = store.search(
            query, embedder, n_results=n, namespace=namespace
        )

    if not results:
        console.print("[yellow]No results.[/yellow]")
        return

    title = f"Search: {query}"
    if namespace:
        title += f"  (namespace: {namespace})"

    table = Table(title=title, show_lines=True, expand=True)
    table.add_column("Score", justify="right", style="bold", no_wrap=True)
    table.add_column("Namespace", style="magenta", no_wrap=True)
    table.add_column("Source", style="cyan", no_wrap=True, max_width=30)
    table.add_column("Text", style="white", overflow="fold")
    for r in results:
        snippet = r.text if len(r.text) < 400 else r.text[:397] + "..."
        table.add_row(
            f"{r.relevance:.2f}",
            r.namespace or "-",
            r.source_file,
            snippet,
        )
    console.print(table)


# ---------------------------------------------------------------------------
# stats
# ---------------------------------------------------------------------------


@app.command("stats")
def cmd_stats(
    data_dir: Path = typer.Option(  # noqa: B008
        _default_data_dir(),
        "--data-dir",
        help="Archive index location.",
    ),
) -> None:
    """Show archive statistics: total chunks and per-namespace breakdown."""
    if not data_dir.exists():
        console.print(f"[yellow]No archive at {data_dir}[/yellow]")
        console.print("Run [cyan]resonant-archive import <dir>[/cyan] first.")
        raise typer.Exit(code=1)

    store = ArchiveStore(data_dir=data_dir)
    total = store.count()
    namespaces = store.list_namespaces()

    console.print(f"[bold]Archive:[/bold]      [cyan]{data_dir}[/cyan]")
    console.print(f"[bold]Total chunks:[/bold] [bold]{total:,}[/bold]")
    console.print()

    if not namespaces:
        console.print("[dim]No namespaces yet. Run `resonant-archive import`.[/dim]")
        return

    table = Table(title="Namespaces", show_header=True, header_style="bold")
    table.add_column("Namespace", style="magenta")
    table.add_column("Chunks", justify="right", style="bold")
    for ns, count in sorted(namespaces.items(), key=lambda x: -x[1]):
        table.add_row(ns, f"{count:,}")
    console.print(table)


# ---------------------------------------------------------------------------
# serve  (HTTP daemon)
# ---------------------------------------------------------------------------


@app.command("serve")
def cmd_serve(
    port: int = typer.Option(  # noqa: B008
        8766, "--port", "-p", help="HTTP port to listen on."
    ),
    data_dir: Path = typer.Option(  # noqa: B008
        _default_data_dir(),
        "--data-dir",
        help="Archive index location.",
    ),
) -> None:
    """Start the HTTP daemon that keeps the embedding model loaded.

    The MCP stdio server (see `resonant-archive mcp`) talks to this daemon
    over HTTP. Leave this running in a terminal while you use Claude Desktop
    or any other MCP-compatible client.
    """
    from .daemon import run_daemon

    if not data_dir.exists():
        console.print(
            f"[yellow]Data directory {data_dir} does not exist — creating it.[/yellow]"
        )
        data_dir.mkdir(parents=True, exist_ok=True)

    console.print(
        f"[bold]Starting resonant-archive daemon[/bold] on port [cyan]{port}[/cyan]"
    )
    console.print(f"  Data directory: [cyan]{data_dir}[/cyan]")
    console.print(f"  Health check:   [cyan]http://localhost:{port}/health[/cyan]")
    console.print("[dim]Press Ctrl+C to stop.[/dim]")
    console.print()
    run_daemon(data_dir=data_dir, port=port)


# ---------------------------------------------------------------------------
# mcp  (stdio MCP server)
# ---------------------------------------------------------------------------


@app.command("mcp")
def cmd_mcp(
    daemon_url: str = typer.Option(  # noqa: B008
        "http://localhost:8766",
        "--daemon-url",
        help="URL of the running resonant-archive daemon.",
    ),
) -> None:
    """Run the MCP stdio server (this is what Claude Desktop invokes).

    Requires the daemon to be running (`resonant-archive serve`). This
    command speaks MCP over stdio and forwards tool calls to the daemon
    over HTTP, so it stays lightweight and spawns instantly.
    """
    from .mcp_server import run_mcp

    run_mcp(daemon_url=daemon_url)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Entry point for the ``resonant-archive`` console script."""
    app()


if __name__ == "__main__":
    main()
