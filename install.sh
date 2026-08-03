#!/bin/bash
# AgentCore Assistant — Local Installer
# Installs the MCP server and skills into a target project directory.
#
# Note: the recommended install is as a Claude Code plugin (see README.md);
# this script is for per-project installs without the plugin system.
#
# Usage:
#   ./install.sh                  # installs into current directory
#   ./install.sh /path/to/project # installs into specified directory

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET_DIR="${1:-.}"
TARGET_DIR="$(cd "$TARGET_DIR" && pwd)"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  AgentCore Assistant — Installer"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Source:  $SCRIPT_DIR"
echo "  Target:  $TARGET_DIR"
echo ""

# Build if not already built
if [ ! -f "$SCRIPT_DIR/dist/index.js" ]; then
  echo "→ Building MCP server..."
  (cd "$SCRIPT_DIR" && npm install && npm run build)
  echo ""
fi

# Write MCP config into .mcp.json at the project root.
# (Claude Code reads project-scoped MCP servers from .mcp.json,
# NOT from .claude/settings.json.)
MCP_FILE="$TARGET_DIR/.mcp.json"
if [ -f "$MCP_FILE" ]; then
  if grep -q '"agentcore"' "$MCP_FILE"; then
    echo "✓ $MCP_FILE already has an 'agentcore' server — leaving it unchanged"
  else
    TMP_FILE=$(mktemp)
    node -e "
      const fs = require('fs');
      const config = JSON.parse(fs.readFileSync(process.argv[1], 'utf-8'));
      config.mcpServers = config.mcpServers || {};
      config.mcpServers.agentcore = {
        command: 'node',
        args: [process.argv[2] + '/dist/index.js']
      };
      config.mcpServers.drawio = config.mcpServers.drawio || {
        command: 'npx',
        args: ['-y', '@drawio/mcp']
      };
      fs.writeFileSync(process.argv[3], JSON.stringify(config, null, 2) + '\n');
    " "$MCP_FILE" "$SCRIPT_DIR" "$TMP_FILE"
    mv "$TMP_FILE" "$MCP_FILE"
    echo "✓ MCP servers (agentcore, drawio) added to existing $MCP_FILE"
  fi
else
  cat > "$MCP_FILE" << EOF
{
  "mcpServers": {
    "agentcore": {
      "command": "node",
      "args": ["$SCRIPT_DIR/dist/index.js"]
    },
    "drawio": {
      "command": "npx",
      "args": ["-y", "@drawio/mcp"]
    }
  }
}
EOF
  echo "✓ Created $MCP_FILE with MCP server config (agentcore, drawio)"
fi

# Copy command file
mkdir -p "$TARGET_DIR/.claude/commands"
CMD_SRC="$SCRIPT_DIR/commands/agentcore.md"
CMD_DST="$TARGET_DIR/.claude/commands/agentcore.md"
if [ -f "$CMD_SRC" ]; then
  cp "$CMD_SRC" "$CMD_DST"
  echo "✓ Command /agentcore installed to $CMD_DST"
else
  echo "⚠  Command file not found at $CMD_SRC — skipping"
fi

# Copy skills (architect, build, deploy, production-readiness)
if [ -d "$SCRIPT_DIR/skills" ]; then
  mkdir -p "$TARGET_DIR/.claude/skills"
  cp -r "$SCRIPT_DIR/skills/." "$TARGET_DIR/.claude/skills/"
  echo "✓ Skills installed to $TARGET_DIR/.claude/skills/"
fi

echo ""
echo "ℹ  Prefer plugin install? From Claude Code run:"
echo "     /plugin marketplace add $SCRIPT_DIR"
echo "     /plugin install aws-agentcore@aws-agentcore-marketplace"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Done! Open Claude Code in $TARGET_DIR"
echo "  (approve the project MCP server when prompted)"
echo ""
echo "  Verify:  /mcp        → should show agentcore + drawio servers"
echo "  Try:     /agentcore  → should invoke the command"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
