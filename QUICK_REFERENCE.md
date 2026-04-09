# Quick Reference

CLI cheat sheet for `resonant-archive`. Full details in `README.md` and `USAGE_GUIDE.md`.

## Install

```bash
pip install resonant-archive          # Python 3.11 or 3.12
resonant-archive --version            # Verify it works
```

## Index a directory

```bash
resonant-archive import <dir> --namespace <name>

# Examples
resonant-archive import ~/Documents/Obsidian --namespace obsidian-vault
resonant-archive import ./chatgpt-markdown --namespace chatgpt-2024
resonant-archive import ~/research --namespace research-notes
```

Options:
- `--namespace, -n` — Descriptive tag for this corpus (defaults to directory name)
- `--data-dir` — Where the archive lives (defaults to `~/.resonant-archive/`)
- `--strategy` — `paragraph` (default, header-aware) or `window` (fixed-size overlap)

## Search from the CLI

```bash
resonant-archive search "your query"

# Filter by namespace
resonant-archive search "identity formation" --namespace chatgpt-2024

# More results
resonant-archive search "relationship patterns" --n-results 10
```

## Stats

```bash
resonant-archive stats
```

Shows total chunks and per-namespace breakdown.

## Daemon + MCP integration

Run the daemon in a terminal (keeps the embedding model loaded for fast MCP queries):

```bash
resonant-archive serve
```

Configure Claude Desktop's MCP (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "resonant-archive": {
      "command": "resonant-archive",
      "args": ["mcp"]
    }
  }
}
```

Restart Claude Desktop. Two tools become available: `archive_search` and `archive_stats`.

## Adding new files later

Just re-run `import` on the same directory (or a new one). Chunks are keyed by their source and index, so re-indexing is idempotent — nothing gets duplicated.

```bash
resonant-archive import ./chatgpt-markdown --namespace chatgpt-2024
```

## Advanced: custom data directory

```bash
resonant-archive import <dir> --data-dir /path/to/custom/store --namespace x
resonant-archive serve --data-dir /path/to/custom/store
resonant-archive search "query" --data-dir /path/to/custom/store
```

## Troubleshooting

| Error | Fix |
|-------|-----|
| `command not found: resonant-archive` | `pip install resonant-archive` or check PATH |
| `cannot reach the resonant-archive daemon` | Run `resonant-archive serve` in a terminal |
| `No archive found at ~/.resonant-archive` | Run `resonant-archive import <dir>` first |
| Slow first search | Normal — the embedding model takes 2-3s to load. Subsequent searches are fast. |
| Python 3.13+ install errors | Use Python 3.11 or 3.12 (ML libs may not have 3.13 wheels yet) |

See `TROUBLESHOOTING.md` for more.

## File locations

- **Archive data:** `~/.resonant-archive/chroma/` (single Chroma file)
- **Embedding model cache:** wherever `sentence-transformers` caches (usually `~/.cache/huggingface/`)
- **Claude Desktop config:**
  - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
  - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
  - Linux: `~/.config/Claude/claude_desktop_config.json`
