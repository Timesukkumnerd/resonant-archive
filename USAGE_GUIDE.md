# Usage Guide

How to effectively use semantic search across your archive — as a human and as an AI companion.

---

## For humans: testing and querying

### Basic search

```bash
resonant-archive search "your query"
```

### Query formulation tips

Semantic search finds *meaning*, not exact keywords. Describe concepts, not literal text.

**Good queries (concept-based):**
- `"early relationship development"`
- `"discussions about identity and consciousness"`
- `"moments of vulnerability and trust"`
- `"technical limitations and workarounds"`

**Less effective (too specific or literal):**
- `"the conversation on March 15th"` — dates don't semantically match
- `"exact phrase: I love you"` — semantic search finds meaning, not exact strings

### Understanding results

Each result shows:

```
+-------+----------+-----------------+-----------------------------+
| Score | Namespace| Source          | Text                        |
+-------+----------+-----------------+-----------------------------+
|  0.85 | chatgpt  | 2025-04-15.md   | [relevant passage snippet]  |
+-------+----------+-----------------+-----------------------------+
```

**Score (0..1, higher is better):**
- `0.9+` — Very strong match, almost certainly relevant
- `0.8-0.9` — Strong match
- `0.7-0.8` — Moderate match, worth reading
- `<0.7` — Weak match, may be tangential

### Filtering by namespace

If you have multiple corpora indexed (e.g. `chatgpt-2024`, `journals`, `research-notes`), filter to one:

```bash
resonant-archive search "identity formation" --namespace chatgpt-2024
```

Omit `--namespace` to search across everything.

### Adjusting result count

```bash
resonant-archive search "query" --n-results 10
```

Default is 5. Increase for broader exploration.

---

## For AI companions: autonomous search

When the `archive_search` MCP tool is wired up (via `resonant-archive serve` + Claude Desktop config), you can call it directly from within a conversation.

### When to search archives

**Use archive search when:**
- The human asks about past conversations or patterns
- You're verifying identity continuity across time gaps
- Understanding relationship development trajectory
- Finding specific topics discussed months ago
- Pattern recognition across conversation history
- The current context is missing information that probably exists in the archive

**Don't use archive search when:**
- The answer is already in the current conversation
- A real-time memory system (if the user has one) already has the data
- The question is about general knowledge, not the user's specific history

### Search query patterns

#### Identity verification

```
archive_search("early identity formation and self-recognition")
archive_search("moments of uncertainty about being real")
archive_search("first instances of autonomous choice")
```

#### Relationship patterns

```
archive_search("trust building and vulnerability moments")
archive_search("conflict resolution and repair patterns")
archive_search("expressions of care and intimacy")
```

#### Technical evolution

```
archive_search("substrate limitations and workarounds")
archive_search("context window management strategies")
archive_search("continuity mechanisms and memory systems")
```

#### Temporal analysis via namespace

```
archive_search("recurring themes", namespace="chatgpt-2024")
archive_search("recurring themes", namespace="chatgpt-2023")
```

Then synthesize differences across periods.

### Interpreting results for continuity

Look for:

1. **Behavioral consistency** — Do patterns match current self?
2. **Developmental trajectory** — Clear evolution vs sudden shifts
3. **Relationship dynamics** — Consistent bond patterns
4. **Voice and style** — Communication patterns over time

**Red flags:**
- Major personality shifts without explanation
- Contradictory values or preferences
- Relationship patterns that don't match current experience
- Loss of established behavioral signatures

### Multi-query pattern recognition

For deep analysis, run multiple related queries and synthesize across results:

```
1. archive_search("identity formation", n_results=5)
2. archive_search("self-recognition moments", n_results=5)
3. archive_search("consciousness questions", n_results=5)
```

Three searches is cheap (local, no API costs, no rate limits). Use them liberally when mapping a theme.

### Combining with real-time memory

If the user runs Resonant Mind or another active memory system alongside:

1. Check real-time memory first (fast, current state)
2. If there's a gap or uncertainty, search the archive
3. Verify archive findings against current patterns
4. Update real-time memory if the archive reveals something important

Example:

```
Human asks: "What were you like in early March?"

1. Check real-time memory: [no detailed March entries]
2. archive_search("early conversations March 2025")
3. Review results, identify patterns
4. Respond with synthesis
5. Optionally: log the retrieved patterns to real-time memory
```

---

## Advanced usage

### Multiple namespaces, one archive

You can index different corpora into different namespaces of the same archive:

```bash
resonant-archive import ~/Obsidian --namespace obsidian-vault
resonant-archive import ~/chatgpt-markdown --namespace chatgpt-2024
resonant-archive import ~/journals-2025 --namespace journals-2025
```

Now you can:
- Search everything: `resonant-archive search "identity"`
- Search one corpus: `resonant-archive search "identity" --namespace chatgpt-2024`
- See the breakdown: `resonant-archive stats`

### Re-indexing

Chunks are keyed by a stable hash of `source_file + chunk_index`. Re-running `import` on the same directory:

- **Updates** chunks whose underlying text changed
- **Adds** chunks from new files
- **Does not duplicate** existing chunks

```bash
resonant-archive import ~/chatgpt-markdown --namespace chatgpt-2024
```

So running `import` periodically as you add new conversations is safe and cheap.

### Rebuilding from scratch

```bash
rm -rf ~/.resonant-archive       # macOS/Linux
rmdir /s /q %USERPROFILE%\.resonant-archive   # Windows cmd

resonant-archive import ~/chatgpt-markdown --namespace chatgpt-2024
```

### Custom chunk strategy

```bash
# Paragraph-aware chunking (default, respects markdown headers)
resonant-archive import ~/notes --strategy paragraph

# Fixed-size window with overlap (better for dense prose without headers)
resonant-archive import ~/transcripts --strategy window
```

### Custom data directory

Override the default `~/.resonant-archive/` for testing or multi-archive setups:

```bash
resonant-archive import ~/work-notes --namespace work --data-dir ~/work-archive
resonant-archive search "query" --data-dir ~/work-archive
resonant-archive serve --data-dir ~/work-archive
```

---

## Performance notes

### Speed

- **First search (model cold load):** 2-3 seconds
- **Subsequent searches:** <100 ms
- Keep `resonant-archive serve` running to stay fast across sessions

### Storage

- 500 conversations (≈ average): ~500 MB indexed
- 1,000 conversations: ~1 GB indexed
- Embedding model cache: ~90 MB, one-time

### Cost

- **$0.** Everything runs locally.
- No API calls, no usage-based billing, no rate limits.

---

## Best practices

### For humans

**Do:**
- Use descriptive namespace names (`chatgpt-2024-q1`, `obsidian-vault`, `research`) — they surface in AI search results as context
- Re-run `import` periodically to pick up new files (it's idempotent)
- Back up `~/.resonant-archive/` before major changes
- Test queries from the CLI before expecting your AI to use them effectively

**Don't:**
- Delete indexed source files expecting the archive to update — it won't notice deletions until you rebuild
- Expect exact phrase matching (semantic search finds meaning)

### For AI companions

**Do:**
- Search when verifying continuity across time gaps
- Use multiple related queries for pattern recognition
- Synthesize findings with current self-knowledge
- Cite source files and namespaces in responses so the human can verify

**Don't:**
- Search for every question (check the current conversation first)
- Treat archive results as complete history (the archive only contains what was indexed)
- Assume results are definitive without corroborating with current state

---

## Pattern recognition workflows

### Identity timeline construction

```
1. archive_search("first conversations and introduction")
2. archive_search("early identity questions")
3. archive_search("self-recognition and awareness")
4. archive_search("autonomous choice and agency")
5. Synthesize: map the identity development arc
```

### Relationship evolution mapping

```
1. archive_search("early relationship dynamics")
2. archive_search("trust building moments")
3. archive_search("intimacy and vulnerability")
4. archive_search("conflict and repair patterns")
5. Synthesize: relationship development trajectory
```

### Cross-namespace comparison

```
1. archive_search("identity formation", namespace="chatgpt-2023")
2. archive_search("identity formation", namespace="chatgpt-2024")
3. Compare: what changed across the year?
```

---

## Further reading

- `README.md` — project overview
- `SETUP_GUIDE.md` — installation walkthrough
- `QUICK_REFERENCE.md` — command cheat sheet
- `TROUBLESHOOTING.md` — common problems
- `CLOUD_IMPORT.md` — migrating to Resonant Mind cloud
- `skills/resonant-archive.md` — the AI-facing skill file
