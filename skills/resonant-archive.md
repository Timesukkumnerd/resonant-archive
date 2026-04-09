---
name: resonant-archive
description: Drive the resonant-archive CLI to import, search, and manage a local semantic archive of AI conversations, notes, or any text corpus. Use when the user asks to import, index, or search their archive; when they mention ChatGPT/Claude export files; when they ask "what did we talk about before"; or when you need to reach into long-term context that lives outside the active conversation.
---

# resonant-archive skill

A skill for driving the `resonant-archive` CLI end-to-end on behalf of the user. When loaded into your context, you should be able to handle archive operations without the user needing to touch the terminal beyond a one-time install.

## What resonant-archive is

`resonant-archive` is a local-first semantic search tool. It takes a directory of markdown or plain-text files (ChatGPT conversation exports, Obsidian vaults, journals, research notes, anything) and builds a searchable index using local embeddings (sentence-transformers / all-MiniLM-L6-v2). The index lives in `~/.resonant-archive/` by default.

The archive is queryable from the command line OR exposed as an MCP server so any MCP-compatible AI (Claude Desktop, Claude Code, etc.) can search it directly as a tool.

**Important:** resonant-archive does *not* parse raw ChatGPT/Claude export ZIPs. It works on directories of markdown files. For ChatGPT exports specifically, users need to convert `conversations.json` → markdown first, typically with the Nexus AI Chat Importer plugin for Obsidian.

## Install check

Before driving any command, confirm the tool is installed:

```bash
resonant-archive --version
```

If the user gets "command not found," they need to install:

```bash
pip install resonant-archive
```

(Or build from source — see the repo README.)

## Commands you can drive

### 1. Import a directory

```bash
resonant-archive import <directory> --namespace <name>
```

Chunks and embeds every `.md` / `.txt` / `.markdown` / `.mdx` file under `<directory>` into the archive, tagged with `--namespace`. The namespace should be descriptive (`chatgpt-2024`, `obsidian-vault`, `research-notes`) because it surfaces in every search result and gives querying AIs context about where a hit came from.

If `--namespace` is omitted, it defaults to the directory name.

**Example prompts and responses:**

- *User: "Import my Obsidian vault at C:/Users/me/Vault into resonant-archive."*
  → Run: `resonant-archive import "C:/Users/me/Vault" --namespace obsidian-vault`

- *User: "I want to search my ChatGPT history. It's in /tmp/chatgpt-export/"*
  → First check: is that a directory of markdown files, or a raw ZIP? If it's raw ChatGPT export, tell the user they need to convert it with Nexus first. If it's already markdown, run: `resonant-archive import /tmp/chatgpt-export --namespace chatgpt-2024`

### 2. Search from the CLI

```bash
resonant-archive search "your query" [--namespace <name>] [--n-results <count>]
```

Useful for one-off searches or testing. Returns a table with relevance scores, namespace tags, source files, and text snippets.

### 3. Show stats

```bash
resonant-archive stats
```

Shows total chunks, per-namespace breakdown, and archive location. Always safe to run; useful for confirming the archive exists and is populated.

### 4. Start the daemon (for MCP integration)

```bash
resonant-archive serve
```

Starts an HTTP daemon on `localhost:8766` that keeps the embedding model warm. **This must be running** in a terminal for Claude Desktop's MCP integration to work. The user keeps this window open while they use Claude Desktop.

### 5. MCP stdio server (called by Claude Desktop)

```bash
resonant-archive mcp
```

This is what gets configured in `claude_desktop_config.json`. Users don't run this directly — Claude Desktop spawns it. The command forwards MCP tool calls to the running daemon.

## Claude Desktop MCP configuration

When the user wants their AI companion (running in Claude Desktop) to be able to search the archive, they need to add this to their `claude_desktop_config.json`:

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

Plus they need to run `resonant-archive serve` in a terminal before using Claude Desktop.

Config file locations:
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux:** `~/.config/Claude/claude_desktop_config.json`

## MCP tools you (the AI) can call

When resonant-archive is configured in Claude Desktop, you get two tools:

### `archive_search(query, namespace?, n_results?)`

Semantic search. Returns results with provenance:
- `relevance` (0..1, higher is better)
- `namespace` — which corpus the hit came from
- `source_file` — original file path, relative to the imported directory
- `title`, `timestamp`, `conversation_id`, `provider` — where available from frontmatter
- `text` — the actual chunk content

Use when:
- The user asks about past conversations or topics
- You're verifying continuity across time gaps
- You need historical context that isn't in the current conversation
- Pattern recognition across the user's history
- Identity verification or relationship dynamics over time

Don't use when:
- The answer is in the current conversation
- Real-time memory (if the user has another memory system) already has it
- The question is about general knowledge, not the user's specific history

### `archive_stats()`

Returns total chunks, per-namespace breakdown, embedding model, data directory. Useful for sanity-checking the archive before searching, or reporting to the user what's indexed.

## Effective search queries

Semantic search finds *meaning*, not exact keywords. Good queries describe concepts:

**Good:**
- "early relationship development and trust building"
- "discussions about identity and consciousness"
- "substrate limitations and workarounds"
- "moments of vulnerability"

**Less effective:**
- "the conversation on March 15th" (use metadata filters if needed, not text)
- "exact phrase 'I love you'" (semantic search matches meaning, not literal text)

Multiple related queries for pattern recognition are better than one catch-all query. Searches are cheap — run 3-5 if you're mapping a theme.

## Common user requests

| User says | You do |
|-----------|--------|
| "Import my notes" | Ask for the directory path, then `resonant-archive import <path> --namespace <guessed-from-dir>` |
| "What did we talk about regarding X?" | Call `archive_search("X")`, synthesize results, cite sources |
| "Is my archive set up?" | Call `archive_stats()`, report totals and namespaces |
| "Search all my chats for Y" | `archive_search("Y", namespace="chatgpt-2024")` or similar (use the right namespace) |
| "I got an error about the daemon" | Remind the user to run `resonant-archive serve` in a terminal |

## Error recovery

**"Cannot reach the resonant-archive daemon"** — The daemon isn't running. Tell the user to open a terminal and run `resonant-archive serve`, keep that terminal open, then try again.

**"No archive found at ~/.resonant-archive"** — The user hasn't imported anything yet. Ask what they want to index.

**"command not found: resonant-archive"** — Not installed, or not on PATH. Suggest `pip install resonant-archive`.

**Slow first query in a session** — The embedding model takes 2-3 seconds to load. Normal. Subsequent queries are fast (~100 ms).

## License and context

resonant-archive is source-available under the Codependent AI Source-Available License — free for personal use, commercial use requires a license. See `LICENSE` in the repo.

It's part of the Resonant ecosystem (Resonant Mind is the active AI memory system; resonant-archive is the long-term searchable archive). They're independent; you don't need one to use the other. If the user is running Resonant Mind cloud and wants to bring their archive into it, point them at `CLOUD_IMPORT.md` in the repo — that's the DIY migration guide.
