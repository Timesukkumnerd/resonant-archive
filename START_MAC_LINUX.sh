#!/usr/bin/env bash
# resonant-archive launcher for Mac/Linux
# Run with: bash START_MAC_LINUX.sh
# Or make executable: chmod +x START_MAC_LINUX.sh

echo "================================================"
echo "  resonant-archive daemon launcher"
echo "================================================"
echo ""
echo "This window keeps the embedding model loaded so"
echo "MCP queries from Claude Desktop stay fast."
echo ""
echo "Leave it open while you use the archive."
echo "Press Ctrl+C to stop when you're done."
echo ""
echo "================================================"
echo ""

# Check resonant-archive is installed
if ! command -v resonant-archive >/dev/null 2>&1; then
    echo "ERROR: resonant-archive is not installed or not on PATH."
    echo ""
    echo "Install with:"
    echo "    pip install resonant-archive"
    echo ""
    echo "See SETUP_GUIDE.md for details."
    exit 1
fi

resonant-archive serve
