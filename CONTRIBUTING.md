# Contributing to resonant-archive

Thanks for your interest in contributing. `resonant-archive` is a small, focused tool — the architecture is opinionated and kept deliberately minimal. This guide helps you contribute effectively.

## How to reach us

- **Bug reports** — [GitHub Issues](https://github.com/codependentai/resonant-archive/issues)
- **Feature proposals** — [GitHub Issues](https://github.com/codependentai/resonant-archive/issues) (open an issue before writing code for anything non-trivial)
- **Questions & discussion** — [GitHub Discussions](https://github.com/codependentai/resonant-archive/discussions) (if enabled)
- **Commercial licensing / partnership** — [codependentai.io](https://codependentai.io)
- **Updates** — Follow [@codependentai](https://tiktok.com/@codependentai) on TikTok

## What we welcome

These can go straight to a PR:

- **Bug fixes** — with a clear description of what was broken and how you fixed it
- **Documentation** — typos, clarifications, better examples, corrections
- **Additional tests** — coverage for edge cases we haven't thought of
- **Platform fixes** — Windows / macOS / Linux path-handling or file-locking quirks
- **Small DX improvements** — better error messages, clearer CLI help text, progress bar tweaks

## What needs an issue first

Open a GitHub Issue to discuss before writing code:

- **New CLI commands** — the command surface is intentionally small; adding one affects the whole UX
- **New file formats** (PDF, DOCX, HTML) — these require new dependencies and careful thought about how to chunk them
- **New embedding models as defaults** — changing the default invalidates existing indexes
- **New vector store backends** — Chroma + `PersistentClient` was chosen deliberately; any alternative would need to justify the trade-off
- **New dependencies** — we keep the dependency tree intentionally small
- **Cloud features** — `resonant-archive` is local-first by design. Automated cloud migration is already planned but the DIY path lives in `CLOUD_IMPORT.md` for now

## Help wanted

Areas where we'd especially appreciate contributions:

- **Automated cloud migration** — the `resonant-archive push --mind-url <url>` flow described in `CLOUD_IMPORT.md`. Currently all manual.
- **Tokenizer-aware chunking** — current chunking is character-based with safe margins. A tokenizer-aware version would produce tighter chunks and avoid edge-case truncation in the embedding model.
- **PDF / DOCX / HTML ingestion** — carefully scoped (no heavy dependencies bundled by default, maybe optional extras)
- **Incremental re-indexing** — detecting changed files and only re-embedding those, instead of processing everything on every `import`
- **Benchmarks** — reproducible retrieval quality benchmarks so we can measure regressions and compare to other tools

If any of these interest you, open an issue to discuss your approach before writing code.

## What we won't accept

The following are architectural decisions, not oversights:

- **Dropping the daemon + MCP split** — we need the daemon to keep the embedding model warm across MCP server spawns. Collapsing them means reloading the model on every Claude Desktop invocation.
- **Bundling a parser for ChatGPT/Claude raw exports** — we explicitly delegate that to upstream tools (Nexus AI Chat Importer, etc.) to avoid a parser maintenance burden for formats we don't control.
- **Cloud-hosted variants** — `resonant-archive` is local-first. That's the point. The `CLOUD_IMPORT.md` guide is for users who want to bridge into their own Resonant Mind deployment.
- **Electron / Tauri wrappers** — the AI-driven workflow via the skill file is the intended UX. Users drive the tool through their AI, not a GUI.

## Development setup

```bash
git clone https://github.com/codependentai/resonant-archive.git
cd resonant-archive

# Recommended: use uv to manage the venv and Python version
uv venv --python 3.12 .venv
source .venv/bin/activate                 # macOS/Linux
.venv/Scripts/activate                    # Windows

# Install in editable mode with dev extras
uv pip install -e ".[dev]"
```

Run the tests:

```bash
pytest tests/
```

All 30 existing tests should pass in ~30 seconds. The store tests download the `all-MiniLM-L6-v2` model on first run (~90 MB), cached afterward.

Try the CLI end-to-end:

```bash
resonant-archive --help
resonant-archive import ./some-markdown-dir --namespace dev
resonant-archive stats
resonant-archive search "a probe query"
```

## PR guidelines

- **One thing per PR.** Bug fix? One PR. New test? One PR. Don't bundle unrelated changes.
- **Describe what and why.** Not just what you changed — why it matters.
- **Run the tests.** `pytest tests/` must pass before you submit.
- **Add tests when it makes sense.** Especially for new chunker behavior, new store operations, or new CLI flags.
- **Match the existing style.** Look at the code around your change and follow the same patterns.
- **No AI-generated code without review.** If you used an AI to write it, review it thoroughly. We will.
- **No generated diffs in the commit.** Keep whitespace-only diffs out of PRs unless that's literally the purpose of the PR.

## Code style

- **Python 3.11+ syntax.** Use `str | None` instead of `Optional[str]`, `list[int]` instead of `List[int]`.
- **Strict typing** throughout `resonant_archive/`. No `Any` without a good reason.
- **Dataclasses** for structured data, not dictionaries.
- **Docstrings** on public functions and classes. Keep them concise — what and why, not how.
- **No defensive validation** for internal code — trust the types. Validate only at system boundaries (CLI input, file I/O, HTTP).
- **Functions over classes** where possible. Classes are for stateful things (the store, the embedder), not for code organization.

## License

By contributing, you agree that your contributions will be licensed under the [Codependent AI Source-Available License](LICENSE) and that copyright in your contributions will be assigned to Codependent AI.
