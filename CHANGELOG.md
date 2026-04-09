# Changelog

All notable changes to `resonant-archive` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-04-09

Initial public release. Modernized from an earlier internal tool (`vault-archive-product`) that was built, shelved during a cloud migration, and revived for this release.

### Added

- **Python 3.11/3.12 package** with `pyproject.toml`, `setuptools` backend, and a `resonant-archive` console script entry point
- **`resonant-archive import`** — chunks and embeds a directory of markdown or text files into a local semantic archive, tagged with a user-supplied namespace
- **`resonant-archive search`** — command-line semantic search with optional namespace filtering and rich table output
- **`resonant-archive stats`** — per-namespace chunk counts and archive location
- **`resonant-archive serve`** — FastAPI daemon that keeps the embedding model warm for fast MCP queries
- **`resonant-archive mcp`** — stdio MCP server (for Claude Desktop) forwarding tool calls to the daemon over HTTP
- **Frontmatter-aware chunker** with two strategies:
  - `paragraph` (default) — header-aware greedy packing with tail merging
  - `window` — fixed-size character windows with overlap and no-gap guarantees
- **Tiered metadata model** — every chunk carries stable `chunk_id`, `source_file`, `chunk_index`, and `char_offset`; plus optional `title`, `timestamp`, `tags`, and Nexus-style `conversation_id` / `provider` when extractable from frontmatter
- **Namespace tagging** — every chunk is stored with a namespace metadata field; results surface the namespace so querying AIs know where a hit came from
- **MCP tools** — `archive_search(query, namespace?, n_results?)` and `archive_stats()`, both exposed via stdio MCP server
- **Skill file** (`skills/resonant-archive.md`) — drops into any MCP-compatible AI's context to enable natural-language operation
- **Comprehensive docs** — `README`, `START_HERE`, `SETUP_GUIDE`, `USAGE_GUIDE`, `QUICK_REFERENCE`, `TROUBLESHOOTING`, `CLOUD_IMPORT`
- **Cross-platform launcher scripts** — `START_WINDOWS.bat` and `START_MAC_LINUX.sh` for double-click daemon startup
- **30 unit tests** covering the chunker (19) and store (11), including semantic similarity verification and namespace isolation

### Technical choices

- **Embedding model:** `sentence-transformers/all-MiniLM-L6-v2` (384-dim, ~90 MB, fast). Alternatives documented in README.
- **Vector store:** `chromadb.PersistentClient` — embedded, file-based, single process, no separate server
- **MCP framework:** Official Python `mcp` SDK
- **CLI framework:** `typer` with `rich` for progress bars and tables
- **Frontmatter parser:** `python-frontmatter` (handles YAML frontmatter with graceful fallback)

### Licensed under

[Codependent AI Source-Available License](LICENSE) — free for personal, educational, and non-commercial use with attribution. Commercial use requires a license.

[Unreleased]: https://github.com/codependentai/resonant-archive/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/codependentai/resonant-archive/releases/tag/v0.1.0
