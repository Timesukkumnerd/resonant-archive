# Cloud Import — Bringing Your Archive Into Resonant Mind

This document is for users who have been running `resonant-archive` locally and want to **promote some or all of their archive into a running Resonant Mind cloud deployment**. This is a DIY path — automated cloud ingestion is planned for a later release, but for now you build it yourself using the pieces documented here.

## Why you might want this

**Stay local.** Your local `resonant-archive` is free, private, and fast. For most users, that's the end of the story — you don't need to do anything in this document.

**Upgrade to cloud.** If you're running Resonant Mind in the cloud and want your long-term archive to live alongside your active memory (so the mind can query them in a unified way), you can migrate selectively by re-embedding your chunks with Gemini and writing them into a dedicated archive table in your Mind deployment.

The design principle: **archive entries in cloud Mind are cognitively inert.** They sit in their own table, don't count as active observations, don't feed the subconscious daemon, don't affect mood or surfacing pools. They're a library the mind can *visit*, not a flood it has to wade through.

## The pieces you need

1. **The `chunks.jsonl` canonical format** produced by `resonant-archive` — one row per chunk, small metadata, human-readable
2. **A new `archive_entries` table** in your Resonant Mind database (schema below)
3. **A re-embedding step** using Gemini (so the vectors match your active mind's embedding space)
4. **A bulk-ingest endpoint** on your Resonant Mind deployment (you add this to the main repo)
5. **A search tool** (`mind_archive_search`) exposed via MCP, wired to the new table

This document gives you the schema, field mappings, and worked examples. The actual endpoint wiring is a change to Resonant Mind proper, which we're deliberately not building in resonant-archive.

---

## Canonical format: `chunks.jsonl`

Every chunk `resonant-archive` produces can be serialized to a JSONL manifest. The schema:

| Field | Type | Tier | Notes |
|-------|------|------|-------|
| `chunk_id` | string | always | Stable sha256-derived 16-char hex |
| `source_file` | string | always | Path relative to the imported directory |
| `text` | string | always | The chunk's actual content |
| `chunk_index` | integer | always | Ordinal of this chunk within its source file |
| `char_offset` | integer | always | Byte offset into the source file body |
| `title` | string | optional | From frontmatter `title` or filename |
| `timestamp` | string | optional | ISO-8601 UTC, from frontmatter or filesystem mtime |
| `timestamp_source` | `"frontmatter"` or `"filesystem"` | optional | Provenance of the timestamp |
| `tags` | list[string] | optional | Stored as comma-joined string in Chroma metadata |
| `conversation_id` | string | optional | From Nexus-style frontmatter |
| `provider` | string | optional | `chatgpt`, `claude`, `lechat` (Nexus-style) |

Generate a manifest from a directory using the library API (a dedicated CLI subcommand is planned):

```python
from pathlib import Path
from resonant_archive.chunker import chunk_directory, write_chunks_jsonl

chunks = chunk_directory(Path("~/chatgpt-markdown").expanduser())
write_chunks_jsonl(chunks, Path("./chatgpt-export.jsonl"))
```

`chunks.jsonl` is the **source of truth** for any migration. Embeddings are derived; the manifest is portable and human-readable.

---

## Suggested `archive_entries` table schema

Add this table to your Resonant Mind database (works for both D1/SQLite and Postgres):

```sql
CREATE TABLE archive_entries (
  chunk_id TEXT PRIMARY KEY,
  namespace TEXT NOT NULL,
  source_file TEXT NOT NULL,
  text TEXT NOT NULL,
  chunk_index INTEGER NOT NULL,
  char_offset INTEGER NOT NULL,
  title TEXT,
  timestamp TEXT,              -- ISO-8601 string
  conversation_id TEXT,
  provider TEXT,
  embedding BLOB NOT NULL,     -- Postgres: vector(768) if using pgvector
  imported_at TEXT NOT NULL    -- ISO-8601 string
);

CREATE INDEX idx_archive_namespace ON archive_entries(namespace);
CREATE INDEX idx_archive_timestamp ON archive_entries(timestamp);
CREATE INDEX idx_archive_conversation ON archive_entries(conversation_id);
```

**For Postgres with pgvector**, use `embedding vector(768)` instead of `BLOB` and add an HNSW index:

```sql
CREATE INDEX idx_archive_embedding
  ON archive_entries
  USING hnsw (embedding vector_cosine_ops);
```

**Critical design constraint:** the archive table is separate from your `observations` table. The subconscious daemon, mood analysis, surfacing pools, and consolidation must all ignore it. Archive entries are library material, not lived memory.

---

## Re-embedding with Gemini

Your local `resonant-archive` uses `all-MiniLM-L6-v2` (384 dimensions). Resonant Mind's cloud deployment uses `Gemini Embedding 2` (768 dimensions by default). These are incompatible vector spaces — you cannot use local embeddings in cloud and vice versa. You have to re-embed.

This costs money (user's own Gemini API key), but it's a one-time cost per chunk. For a 50 MB archive (~50,000 chunks), expect roughly **$3-8 in Gemini embedding costs** at current pricing. Check Gemini's pricing page for the latest numbers.

Example re-embedding script:

```python
import json
from pathlib import Path
import google.generativeai as genai

genai.configure(api_key="YOUR_GEMINI_KEY")

def embed_chunks(jsonl_path: Path, output_path: Path) -> None:
    with open(jsonl_path, "r", encoding="utf-8") as f_in, \
         open(output_path, "w", encoding="utf-8") as f_out:
        batch: list[dict] = []
        for line in f_in:
            batch.append(json.loads(line))
            if len(batch) >= 100:
                _embed_batch(batch, f_out)
                batch = []
        if batch:
            _embed_batch(batch, f_out)

def _embed_batch(batch: list[dict], f_out) -> None:
    texts = [c["text"] for c in batch]
    response = genai.embed_content(
        model="models/text-embedding-004",
        content=texts,
        task_type="retrieval_document",
    )
    for chunk, vector in zip(batch, response["embedding"]):
        chunk["embedding"] = vector
        f_out.write(json.dumps(chunk) + "\n")

embed_chunks(Path("./chatgpt-export.jsonl"), Path("./chatgpt-embedded.jsonl"))
```

The output is a new JSONL with an `embedding` field on each row.

---

## Bulk ingest endpoint (you build this on the Mind side)

Add a new route to your Resonant Mind deployment — something like `POST /api/archive/bulk`. It accepts a JSON body with an array of `archive_entries` records and writes them to the table in a transaction.

Sketch (adapt to your actual framework):

```typescript
// In your Resonant Mind repo
app.post("/api/archive/bulk", async (c) => {
  const body = await c.req.json<{ namespace: string; entries: ArchiveEntry[] }>();
  const db = c.env.DB;

  for (const entry of body.entries) {
    await db.prepare(`
      INSERT INTO archive_entries (
        chunk_id, namespace, source_file, text, chunk_index, char_offset,
        title, timestamp, conversation_id, provider, embedding, imported_at
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      ON CONFLICT(chunk_id) DO UPDATE SET
        text = excluded.text,
        embedding = excluded.embedding,
        imported_at = excluded.imported_at
    `).bind(
      entry.chunk_id,
      body.namespace,
      entry.source_file,
      entry.text,
      entry.chunk_index,
      entry.char_offset,
      entry.title ?? null,
      entry.timestamp ?? null,
      entry.conversation_id ?? null,
      entry.provider ?? null,
      serializeEmbedding(entry.embedding),
      new Date().toISOString(),
    ).run();
  }

  return c.json({ imported: body.entries.length });
});
```

Protect this endpoint with whatever auth your Mind deployment uses.

---

## Exposing `mind_archive_search` as an MCP tool

On the Mind side, add a new MCP tool that queries the archive table and returns results tagged as archive (not observations). Sketch:

```typescript
server.tool(
  "mind_archive_search",
  {
    query: z.string(),
    namespace: z.string().optional(),
    limit: z.number().default(5),
  },
  async ({ query, namespace, limit }) => {
    // 1. Embed the query with Gemini (same model as above)
    const queryEmbedding = await embedQuery(query);

    // 2. Vector search the archive_entries table
    const results = await vectorSearch(
      "archive_entries",
      queryEmbedding,
      { where: namespace ? { namespace } : {}, limit }
    );

    // 3. Return with clear "archive" tagging
    return results.map(r => ({
      source: "archive",
      namespace: r.namespace,
      title: r.title,
      timestamp: r.timestamp,
      text: r.text,
      relevance: r.score,
    }));
  }
);
```

**Keep `mind_archive_search` separate from `mind_search`.** They query different data with different semantics. Your mind's active cognition pulls from observations, not archive.

---

## Critical: exclude archive from daemon + mood + surfacing

Your Mind's subconscious daemon iterates over observations to compute mood, detect patterns, generate proposals, identify hot entities. **These processes must ignore `archive_entries`.**

Concretely, every SQL query in your daemon that reads from `observations` should *not* also read from `archive_entries`. Add comments to make this invariant obvious to future-you:

```sql
-- IMPORTANT: this query deliberately excludes archive_entries.
-- Archive is cognitively inert — library material, not lived memory.
SELECT * FROM observations WHERE ...;
```

This is the whole point of the separation. Break it and the archive pollutes your mind's active state.

---

## Suggested migration workflow

1. Build your local archive as usual: `resonant-archive import <dir> --namespace <name>`
2. Verify it: `resonant-archive search "a probe query"` returns what you expect
3. Export to JSONL: use the library API as shown above
4. Re-embed with Gemini (costs money, measure first on a small subset)
5. Bulk ingest to your Mind via `POST /api/archive/bulk`
6. Verify in Mind: `mind_archive_search` returns results
7. (Optional) Delete the local Chroma index if you only want cloud now — but the JSONL manifest is worth keeping as a source of truth

---

## Questions to think about before you migrate

- **Do you actually need it in cloud?** Local archive is free and fast. Cloud archive only makes sense if you want unified querying alongside active mind memory.
- **What subset?** You probably don't want your entire ChatGPT history in cloud. Consider filtering to specific namespaces, date ranges, or manually curated subsets before re-embedding.
- **Can you afford the embedding cost?** Measure on a small batch first (100 chunks ≈ $0.01-0.05).
- **Is your Mind deployment ready?** You need the table schema, the bulk endpoint, and the MCP tool in place before you can ingest anything.

If any of these give you pause, **stay local**. `resonant-archive` is designed to be valuable on its own without cloud integration.

---

## Future: automated migration

A `resonant-archive push --mind-url <url>` command is planned for a later release. It will handle manifest export, re-embedding with Gemini, and bulk ingest in one pipeline. For now, this document is the manual path.

If you build a nice wrapper for this workflow yourself, PRs are welcome.
