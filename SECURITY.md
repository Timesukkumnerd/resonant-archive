# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |

## Reporting a vulnerability

**Do not open a public issue for security vulnerabilities.**

DM us on [X (@codependent_ai)](https://x.com/codependent_ai) or message the [Telegram channel](https://t.me/+xSE1P_qFPgU4NDhk) with:

- Description of the vulnerability
- Steps to reproduce
- Impact assessment (what an attacker could do)

We'll acknowledge within 48 hours and aim to patch critical issues within 7 days.

## Security model

`resonant-archive` is **local-first** software that runs on your machine:

- **No cloud backend** — the archive is a single ChromaDB directory at `~/.resonant-archive/` by default. Your data stays local.
- **No telemetry** — nothing phones home. The only network traffic is the one-time embedding model download from HuggingFace on first use.
- **No authentication** — the daemon binds to `127.0.0.1` only. It's not designed to be exposed over a network.
- **No API keys required** — embeddings run locally via `sentence-transformers`. There's no third-party service being called.
- **Your content is your own** — indexed text stays in your local Chroma store. We can't see it.

### What to watch for

- **Do not expose the daemon port** (`8766` by default) over the public internet. It has no authentication and isn't designed for remote access. If you need remote access, put a reverse proxy with authentication in front of it.
- **Be careful what you index.** If your notes contain secrets, API keys, passwords, or private third-party data, those will land in the Chroma store and be retrievable via semantic search. `resonant-archive` preserves everything it's given — it's not an access-control layer.
- **The daemon writes to disk.** The default location is `~/.resonant-archive/`. On shared machines, make sure the directory has appropriate permissions.
- **Do not commit `~/.resonant-archive/` to git.** The `.gitignore` in this repo catches common copies of it, but be aware it exists in your home directory by default.
- **Model cache location** — `sentence-transformers` downloads models to `~/.cache/huggingface/` (or platform equivalent). Treat the cache like any other ML model cache.

### What `resonant-archive` does NOT protect you from

- **Leaking your source files.** If your Obsidian vault has secrets and you index it, those secrets are now in the archive. Curate what you index.
- **MCP clients with broad permissions.** If you expose `archive_search` to an AI that can then be prompt-injected, a hostile prompt could exfiltrate archive content via tool-call output. This is a general MCP concern, not specific to `resonant-archive`.
- **Filesystem compromise.** If an attacker has shell access to your machine, they can read the Chroma database directly and don't need `resonant-archive` at all.

## Reporting scope

We accept reports for issues in:

- The `resonant_archive` Python package (chunker, embedder, store, daemon, MCP server, CLI)
- Documentation that misleads users about security behavior
- The default configurations (listen addresses, permissions, paths)

We don't control and can't fix:

- Bugs in `chromadb`, `sentence-transformers`, `torch`, `fastapi`, or other upstream dependencies (report those to their respective projects, but feel free to mention them to us so we can track)
- Issues in Claude Desktop, Claude Code, or other MCP clients
- Issues in `Nexus AI Chat Importer` (report upstream)
