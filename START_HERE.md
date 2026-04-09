# Getting Started

The short version:

```bash
# 1. Install (one time)
pip install resonant-archive

# 2. Import a directory of markdown or text files
resonant-archive import ~/Documents/MyNotes --namespace my-notes

# 3. Start the daemon in a terminal and leave it running
resonant-archive serve
```

That's it. Your archive is now searchable.

## To use from the command line

```bash
resonant-archive search "what did I think about X"
resonant-archive stats
```

## To use from Claude Desktop

Make sure `resonant-archive serve` is running in a terminal, then add this to your Claude Desktop config (`%APPDATA%\Claude\claude_desktop_config.json` on Windows, `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

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

Restart Claude Desktop. Ask your AI companion to search the archive — it'll call the MCP tool automatically.

## If you have a ChatGPT or Claude export ZIP

`resonant-archive` indexes markdown directories, not raw export ZIPs. Convert the ZIP to markdown first with the [Nexus AI Chat Importer](https://github.com/Superkikim/nexus-ai-chat-importer) Obsidian plugin, then point `resonant-archive import` at the resulting folder.

## Next

- `README.md` — the full overview
- `SETUP_GUIDE.md` — detailed install, troubleshooting
- `USAGE_GUIDE.md` — effective query patterns, AI companion workflows
- `QUICK_REFERENCE.md` — command cheat sheet
- `CLOUD_IMPORT.md` — migrating your archive into a Resonant Mind cloud deployment
- `skills/resonant-archive.md` — drop this into your AI's context for natural-language operation

Need help? See `TROUBLESHOOTING.md` or visit [codependentai.io](https://codependentai.io).
