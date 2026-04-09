"""Tests for resonant_archive.chunker.

Copyright (C) 2025-2026 Codependent AI
Licensed under the Codependent AI Source-Available License. See LICENSE.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Iterator

import pytest

from resonant_archive.chunker import (
    Chunk,
    chunk_directory,
    parse_file,
    split_body,
    write_chunks_jsonl,
)


# ---------------------------------------------------------------------------
# split_body — paragraph strategy
# ---------------------------------------------------------------------------


def test_split_empty_returns_nothing() -> None:
    assert split_body("") == []
    assert split_body("   \n  \n\n  ") == []


def test_split_preserves_offsets() -> None:
    body = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
    chunks = split_body(body, max_chars=50, min_chars=10, overlap_chars=5)
    assert len(chunks) >= 1
    for text, offset in chunks:
        reconstructed = body[offset : offset + len(text)]
        assert reconstructed == text


def test_split_merges_short_paragraphs_under_max() -> None:
    body = "One.\n\nTwo.\n\nThree.\n\nFour."
    chunks = split_body(body)
    assert len(chunks) == 1
    assert "One" in chunks[0][0]
    assert "Four" in chunks[0][0]


def test_split_never_merges_across_headers() -> None:
    body = (
        "Intro paragraph.\n\n"
        "# Section One\n\n"
        "Body of section one.\n\n"
        "# Section Two\n\n"
        "Body of section two."
    )
    chunks = split_body(body, max_chars=10000, min_chars=10)
    header_chunks = [c for c, _ in chunks if c.lstrip().startswith("#")]
    assert len(header_chunks) >= 2


def test_split_long_paragraph_into_windows() -> None:
    long_text = "word " * 500  # ~2500 chars
    chunks = split_body(
        long_text, max_chars=500, min_chars=100, overlap_chars=50
    )
    assert len(chunks) > 1
    for text, _ in chunks:
        assert len(text) <= 500


# ---------------------------------------------------------------------------
# split_body — window strategy
# ---------------------------------------------------------------------------


def test_window_short_input_single_chunk() -> None:
    chunks = split_body(
        "short text", strategy="window", max_chars=100, overlap_chars=10
    )
    assert chunks == [("short text", 0)]


def test_window_overlapping_no_gaps() -> None:
    body = "a " * 1000  # 2000 chars
    chunks = split_body(
        body, strategy="window", max_chars=500, overlap_chars=50
    )
    assert len(chunks) > 1
    for text, _ in chunks:
        assert len(text) <= 500
    # Adjacent chunks must overlap (no gaps).
    for i in range(1, len(chunks)):
        prev_text, prev_off = chunks[i - 1]
        _, cur_off = chunks[i]
        assert cur_off < prev_off + len(prev_text)
    # Last chunk reaches the end of the body.
    last_text, last_off = chunks[-1]
    assert last_off + len(last_text) == len(body)


# ---------------------------------------------------------------------------
# parse_file
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_dir() -> Iterator[Path]:
    with tempfile.TemporaryDirectory(prefix="resonant-archive-test-") as d:
        yield Path(d)


def test_parse_plain_markdown_no_frontmatter(tmp_dir: Path) -> None:
    path = tmp_dir / "plain.md"
    path.write_text("# Hello\n\nSome body text.", encoding="utf-8")
    parsed = parse_file(path)
    assert "# Hello" in parsed.body
    assert "Some body text." in parsed.body
    assert parsed.metadata["title"] == "plain"
    assert parsed.metadata["timestamp_source"] == "filesystem"


def test_parse_frontmatter_extraction(tmp_dir: Path) -> None:
    path = tmp_dir / "journal.md"
    content = (
        "---\n"
        "title: My Journal Entry\n"
        "date: 2024-03-15T10:30:00Z\n"
        "tags: [personal, journal]\n"
        "---\n\n"
        "Today was a good day."
    )
    path.write_text(content, encoding="utf-8")
    parsed = parse_file(path)
    assert parsed.metadata["title"] == "My Journal Entry"
    assert parsed.metadata["timestamp"].startswith("2024-03-15T10:30:00")
    assert parsed.metadata["timestamp_source"] == "frontmatter"
    assert parsed.metadata["tags"] == ["personal", "journal"]
    assert parsed.body.strip() == "Today was a good day."


def test_parse_nexus_style_conversation(tmp_dir: Path) -> None:
    path = tmp_dir / "conversation.md"
    content = (
        "---\n"
        "nexus: nexus-ai-chat-importer\n"
        "provider: chatgpt\n"
        "conversation_id: abc-123-def\n"
        "create_time: 1710000000\n"
        "title: Debugging session\n"
        "---\n\n"
        "## User\n\n"
        "How do I fix this bug?\n\n"
        "## ChatGPT\n\n"
        "Try turning it off and on again."
    )
    path.write_text(content, encoding="utf-8")
    parsed = parse_file(path)
    assert parsed.metadata["conversation_id"] == "abc-123-def"
    assert parsed.metadata["provider"] == "chatgpt"
    assert parsed.metadata["title"] == "Debugging session"
    assert parsed.metadata["timestamp"].startswith("2024-03-09T16:00:00")
    assert parsed.metadata["timestamp_source"] == "frontmatter"


def test_parse_malformed_frontmatter_falls_back(tmp_dir: Path) -> None:
    path = tmp_dir / "broken.md"
    path.write_text(
        "---\nnot: valid: yaml: here: oops\n---\nBody.", encoding="utf-8"
    )
    parsed = parse_file(path)
    assert isinstance(parsed.body, str)
    assert parsed.metadata["title"] == "broken"


# ---------------------------------------------------------------------------
# chunk_directory
# ---------------------------------------------------------------------------


@pytest.fixture
def fixture_dir(tmp_dir: Path) -> Path:
    (tmp_dir / "note1.md").write_text(
        "# First Note\n\nFirst paragraph.\n\nSecond paragraph.",
        encoding="utf-8",
    )
    (tmp_dir / "note2.txt").write_text(
        "Plain text file contents.", encoding="utf-8"
    )
    subdir = tmp_dir / "subdir"
    subdir.mkdir()
    (subdir / "nested.md").write_text(
        "---\ntitle: Nested\n---\n\nNested content.", encoding="utf-8"
    )
    (tmp_dir / ".hidden.md").write_text("should not appear", encoding="utf-8")
    hidden_dir = tmp_dir / ".hidden_dir"
    hidden_dir.mkdir()
    (hidden_dir / "hidden.md").write_text("also not", encoding="utf-8")
    return tmp_dir


def test_walk_finds_markdown_and_text_recursively(fixture_dir: Path) -> None:
    chunks = chunk_directory(fixture_dir)
    sources = {c.source_file for c in chunks}
    assert "note1.md" in sources
    assert "note2.txt" in sources
    assert "subdir/nested.md" in sources


def test_walk_skips_hidden_files_and_dirs(fixture_dir: Path) -> None:
    chunks = chunk_directory(fixture_dir)
    sources = {c.source_file for c in chunks}
    assert not any(".hidden" in s for s in sources)


def test_walk_respects_extensions(fixture_dir: Path) -> None:
    chunks = chunk_directory(fixture_dir, extensions=(".txt",))
    sources = {c.source_file for c in chunks}
    assert sources == {"note2.txt"}


def test_stable_chunk_ids_across_runs(fixture_dir: Path) -> None:
    first = [c.chunk_id for c in chunk_directory(fixture_dir)]
    second = [c.chunk_id for c in chunk_directory(fixture_dir)]
    assert first == second


def test_title_derivation(fixture_dir: Path) -> None:
    chunks = chunk_directory(fixture_dir)
    nested = next(c for c in chunks if c.source_file == "subdir/nested.md")
    assert nested.title == "Nested"  # from frontmatter
    plain = next(c for c in chunks if c.source_file == "note2.txt")
    assert plain.title == "note2"  # from filename


# ---------------------------------------------------------------------------
# write_chunks_jsonl
# ---------------------------------------------------------------------------


def test_write_jsonl_format(tmp_dir: Path) -> None:
    chunks = [
        Chunk(
            chunk_id="a",
            source_file="x.md",
            text="hello",
            chunk_index=0,
            char_offset=0,
        ),
        Chunk(
            chunk_id="b",
            source_file="x.md",
            text="world",
            chunk_index=1,
            char_offset=6,
        ),
    ]
    out = tmp_dir / "out.jsonl"
    write_chunks_jsonl(chunks, out)
    content = out.read_text(encoding="utf-8")
    lines = content.strip().split("\n")
    assert len(lines) == 2
    assert json.loads(lines[0])["chunk_id"] == "a"
    assert json.loads(lines[1])["chunk_id"] == "b"
    assert content.endswith("\n")


def test_write_jsonl_empty(tmp_dir: Path) -> None:
    out = tmp_dir / "empty.jsonl"
    write_chunks_jsonl([], out)
    assert out.read_text(encoding="utf-8") == ""


def test_to_dict_omits_none_fields() -> None:
    chunk = Chunk(
        chunk_id="x",
        source_file="y.md",
        text="hello",
        chunk_index=0,
        char_offset=0,
        title="Y",
    )
    d = chunk.to_dict()
    assert "title" in d
    assert "timestamp" not in d
    assert "conversation_id" not in d
