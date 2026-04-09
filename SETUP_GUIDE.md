# Setup Guide

Full installation walkthrough for `resonant-archive`.

## Prerequisites

- **Python 3.11 or 3.12.** Python 3.13+ may still have wheel issues with some ML libraries (`torch`, `sentence-transformers`, `chromadb`). If in doubt, use 3.12.
- **~2 GB disk space** for the embedding model, Python deps, and a small test archive. More for larger corpora.
- **Windows, macOS, or Linux.** Tested primarily on Windows.
- **Claude Desktop** (optional, only needed if you want MCP integration).

## Step 1: Check your Python version

```bash
python --version
```

Expect `Python 3.11.x` or `Python 3.12.x`.

If you have 3.13+, install 3.12 alongside it:

```bash
# Windows
winget install Python.Python.3.12

# macOS
brew install python@3.12

# Debian/Ubuntu
sudo apt install python3.12 python3.12-venv
```

Or use [`uv`](https://docs.astral.sh/uv/), which can manage Python versions for you:

```bash
uv python install 3.12
```

## Step 2: Create a virtual environment (recommended)

Keeps `resonant-archive`'s dependencies separate from your system Python.

### Using standard venv

```bash
python3.12 -m venv ~/.venvs/resonant-archive
# Activate:
source ~/.venvs/resonant-archive/bin/activate    # macOS/Linux
~/.venvs/resonant-archive/Scripts/activate       # Windows (PowerShell)
```

### Using uv (faster, recommended)

```bash
uv venv --python 3.12 ~/.venvs/resonant-archive
source ~/.venvs/resonant-archive/bin/activate    # or Windows equivalent
```

## Step 3: Install resonant-archive

```bash
pip install resonant-archive
```

Or from source:

```bash
git clone <repo-url> resonant-archive
cd resonant-archive
pip install -e .
```

First install downloads:
- `resonant-archive` itself (tiny)
- `sentence-transformers`, `torch`, `transformers` (larger — ~500 MB)
- `chromadb`, `fastapi`, `uvicorn`, `mcp`, `typer`, `rich` (smaller)

Expected time: 5-15 minutes depending on network.

Verify:

```bash
resonant-archive --version
resonant-archive --help
```

## Step 4: Prepare your text files

`resonant-archive` works on directories of `.md` / `.txt` / `.markdown` / `.mdx` files. A few common starting points:

### A. Obsidian vault

Already markdown. Point `resonant-archive` at the vault directory.

```bash
resonant-archive import "C:/Users/You/Documents/Obsidian Vault" --namespace obsidian
```

### B. Plain notes folder

Any folder of markdown or text files. Subdirectories are walked recursively.

```bash
resonant-archive import ~/Documents/Notes --namespace notes
```

### C. ChatGPT conversation export

ChatGPT's export is a ZIP containing `conversations.json`. `resonant-archive` doesn't parse raw JSON — convert it to markdown first.

**Recommended: [Nexus AI Chat Importer](https://github.com/Superkikim/nexus-ai-chat-importer)** — an Obsidian plugin that converts ChatGPT (and Claude, and Le Chat) exports into individual markdown files with rich frontmatter (conversation_id, provider, create_time, title). The frontmatter is perfect for `resonant-archive` — every chunk keeps its conversation metadata.

Workflow:

1. Install Obsidian (https://obsidian.md) and open any vault
2. Install the "Nexus AI Chat Importer" community plugin
3. Run it on your ChatGPT export ZIP — output goes into your vault as individual `.md` files
4. Point `resonant-archive` at the resulting folder:

```bash
resonant-archive import "~/Obsidian/AI Chat Imports" --namespace chatgpt-2024
```

### D. Claude conversation export

Claude's export is already markdown-friendly. Save each conversation as a separate `.md` file, put them in a folder, and import:

```bash
resonant-archive import ~/claude-conversations --namespace claude-2024
```

## Step 5: Run the first import

```bash
resonant-archive import <your-directory> --namespace <descriptive-name>
```

First run:
1. Downloads the embedding model (`all-MiniLM-L6-v2`, ~90 MB) — one time, cached afterward
2. Walks the directory, parses frontmatter, chunks each file
3. Embeds all chunks in batches (progress bar displayed)
4. Writes to `~/.resonant-archive/chroma/`

Expected time:
- 100 files: 1-3 minutes
- 500 files: 5-10 minutes
- 1,000+ files: 10-20 minutes

## Step 6: Verify the import

```bash
resonant-archive stats
```

Shows total chunks and per-namespace breakdown. Example output:

```
Archive:      ~/.resonant-archive
Total chunks: 1,234

Namespaces
+--------------+--------+
| Namespace    | Chunks |
+--------------+--------+
| chatgpt-2024 |    987 |
| obsidian     |    247 |
+--------------+--------+
```

Test a search:

```bash
resonant-archive search "a topic you know is in there"
```

## Step 7: Start the daemon (for MCP)

If you want Claude Desktop (or any other MCP client) to query the archive, the daemon needs to be running. Open a terminal and run:

```bash
resonant-archive serve
```

You'll see:

```
Starting resonant-archive daemon on port 8766
  Data directory: ~/.resonant-archive
  Health check:   http://localhost:8766/health
Press Ctrl+C to stop.

[resonant-archive] daemon starting
[resonant-archive] loading embedding model...
[resonant-archive] ready. model: all-MiniLM-L6-v2
INFO:     Uvicorn running on http://127.0.0.1:8766
```

**Leave this terminal window open.** Close it with Ctrl+C when you're done with your session.

## Step 8: Configure Claude Desktop

Find your Claude Desktop config file:
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

Add the `resonant-archive` block to `mcpServers`:

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

If `resonant-archive` isn't on your PATH (e.g. you installed into a virtualenv), use the full path to the executable. See `claude_desktop_config_example.json` for platform-specific paths.

**Completely quit and reopen Claude Desktop** (not just close the window). Your AI companion should now see two tools: `archive_search` and `archive_stats`.

## Step 9: Test the MCP integration

In Claude Desktop, ask something like:

> *"Search my archive for discussions about identity formation, and summarize what you find."*

Your companion should call `archive_search`, get results back with relevance scores and source files, and synthesize a response.

## Step 10: Give your AI the skill file (optional but recommended)

For the smoothest experience, drop `skills/resonant-archive.md` (included in this repo) into your AI's context as a skill or system instruction. It teaches the AI how to drive the full tool — when to search, how to interpret results, how to recover from errors — so you can interact entirely through natural language.

## Adding new conversations later

Just re-run `import` on the same directory. It's idempotent — nothing duplicates:

```bash
resonant-archive import "~/Obsidian/AI Chat Imports" --namespace chatgpt-2024
```

Or import a completely new directory as a new namespace:

```bash
resonant-archive import ~/journal-2025 --namespace journals-2025
```

## Troubleshooting

See `TROUBLESHOOTING.md` for solutions to common problems.

## Next

- `USAGE_GUIDE.md` — effective query patterns, pattern recognition workflows, AI companion best practices
- `QUICK_REFERENCE.md` — command cheat sheet
- `CLOUD_IMPORT.md` — migrating your local archive into a Resonant Mind cloud deployment
