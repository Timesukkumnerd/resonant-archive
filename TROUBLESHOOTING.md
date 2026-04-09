# Troubleshooting

## Install

### `command not found: resonant-archive`

The package isn't installed or isn't on your PATH.

```bash
pip install resonant-archive
resonant-archive --version
```

If you installed inside a virtualenv, activate it first (`source .venv/bin/activate` on macOS/Linux, `.venv\Scripts\activate` on Windows) or use the full path to the script.

### `pip install` fails on Python 3.13+

`sentence-transformers`, `chromadb`, or `torch` may not have wheels yet for very new Python versions. Use **Python 3.11 or 3.12** instead.

```bash
# Windows (winget)
winget install Python.Python.3.12

# macOS (Homebrew)
brew install python@3.12

# Linux (Debian/Ubuntu)
sudo apt install python3.12
```

Then reinstall with that Python:

```bash
python3.12 -m pip install resonant-archive
```

If you use `uv`, even simpler:

```bash
uv venv --python 3.12 .venv
.venv/bin/pip install resonant-archive   # macOS/Linux
.venv\Scripts\pip install resonant-archive   # Windows
```

### `ModuleNotFoundError: No module named 'sentence_transformers'`

Dependencies didn't install. Try:

```bash
pip install sentence-transformers chromadb fastapi uvicorn mcp httpx pydantic python-frontmatter typer rich
```

## Indexing

### `No text files found. Nothing to index.`

The directory you passed doesn't contain `.md`, `.markdown`, `.mdx`, or `.txt` files (or they're all hidden / in hidden directories). Check:

```bash
ls <your-directory>/*.md   # or *.txt
```

Hidden files (names starting with `.`) and hidden directories are skipped by design.

### First index is slow

Normal. On first run, `resonant-archive` downloads the embedding model (~90 MB) and then embeds every chunk. Rough timing:

- 100 files: 1-3 minutes
- 500 files: 5-10 minutes
- 1,000 files: 10-20 minutes

Subsequent runs are much faster (model is cached).

### Re-running `import` doesn't duplicate anything, right?

Correct. Chunks are keyed by a stable hash of `source_file + chunk_index`, so re-running `import` on the same directory is idempotent. Changed files get updated; new files get added; old files stay.

## Search

### `No archive found at ~/.resonant-archive`

You haven't indexed anything yet. Run `resonant-archive import <dir> --namespace <name>` first.

### Search returns no results

Possible causes:
1. Nothing in the namespace you're filtering on. Run `resonant-archive stats` to see what's indexed.
2. Query is too narrow. Try a broader, concept-level query (see `USAGE_GUIDE.md` for query patterns).
3. The topic isn't actually in your archive.

### Slow first search in a Claude Desktop session

Normal. The embedding model takes 2-3 seconds to load into memory. Subsequent searches in the same session are ~100 ms.

If you want instant first queries too, run `resonant-archive serve` in a terminal — that keeps the model warm between Claude Desktop sessions.

## MCP + Claude Desktop

### "Cannot reach the resonant-archive daemon at http://localhost:8766"

The daemon isn't running. Open a terminal and run:

```bash
resonant-archive serve
```

Leave that terminal open. The MCP server talks to this daemon over HTTP to get fast searches without reloading the embedding model on every Claude Desktop spawn.

### Claude Desktop doesn't see `archive_search` or `archive_stats`

Check, in order:

1. `resonant-archive serve` is running in a terminal
2. Your `claude_desktop_config.json` has the `resonant-archive` MCP entry (see `claude_desktop_config_example.json`)
3. The path in the config is correct — if `resonant-archive` isn't on your PATH, use the full path to the binary
4. You've **completely quit and reopened** Claude Desktop (not just closed the window)

### "Port 8766 already in use"

Another process is on that port. Either stop it, or run on a different port:

```bash
resonant-archive serve --port 8799
```

Then tell the MCP server to use the new port:

```json
{
  "mcpServers": {
    "resonant-archive": {
      "command": "resonant-archive",
      "args": ["mcp", "--daemon-url", "http://localhost:8799"]
    }
  }
}
```

## Data

### Where is the archive stored?

Default location: `~/.resonant-archive/chroma/` (a single Chroma database). Override with `--data-dir` on any command.

### Can I back up the archive?

Yes. Copy the `~/.resonant-archive/` directory. It's self-contained. To restore, copy it back.

### Can I delete and rebuild the archive?

Yes. Delete the `~/.resonant-archive/` directory and re-run `import`. It'll regenerate from your source files.

```bash
rm -rf ~/.resonant-archive       # macOS/Linux
rmdir /s /q %USERPROFILE%\.resonant-archive   # Windows cmd
```

## Getting more help

- `README.md` — overview and quick start
- `SETUP_GUIDE.md` — detailed install instructions
- `USAGE_GUIDE.md` — query patterns and AI companion workflows
- `QUICK_REFERENCE.md` — command cheat sheet
- `CLOUD_IMPORT.md` — migrating to Resonant Mind cloud

For licensing and partnership inquiries: [codependentai.io](https://codependentai.io).
