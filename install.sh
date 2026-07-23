#!/bin/bash
# AgentCore Assistant — Skill Installer
# Copies the agentcore skill into a target project (or your personal skills dir).
#
# The skill is fully self-contained: a dependency-free Python CLI plus Markdown.
# There is nothing to build and no packages to install — you only need Python 3.8+.
#
# Usage:
#   ./install.sh                    # install into ./.claude/skills (current project)
#   ./install.sh /path/to/project   # install into a specific project
#   ./install.sh --global           # install into ~/.claude/skills (all projects)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_SRC="$SCRIPT_DIR/skills/agentcore"

if [ "$1" = "--global" ]; then
  DEST_ROOT="$HOME/.claude/skills"
else
  TARGET_DIR="${1:-.}"
  TARGET_DIR="$(cd "$TARGET_DIR" && pwd)"
  DEST_ROOT="$TARGET_DIR/.claude/skills"
fi

DEST="$DEST_ROOT/agentcore"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  AgentCore Assistant — Skill Installer"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Source:  $SKILL_SRC"
echo "  Target:  $DEST"
echo ""

if ! command -v python3 >/dev/null 2>&1; then
  echo "⚠  Python not found. The skill's knowledge CLI needs Python 3.8+."
  echo "   Install Python, then re-run this script."
  exit 1
fi

if [ ! -f "$SKILL_SRC/SKILL.md" ]; then
  echo "⚠  Could not find the skill at $SKILL_SRC"
  exit 1
fi

mkdir -p "$DEST_ROOT"
rm -rf "$DEST"
cp -R "$SKILL_SRC" "$DEST"

echo "✓ Skill 'agentcore' installed."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Done! Open Claude Code and try:"
echo ""
echo "    \"What components does AgentCore have?\""
echo "    \"Build me a customer support agent with memory\""
echo ""
echo "  The skill triggers automatically on AgentCore topics."
echo "  Verify the CLI:"
echo "    python3 \"$DEST/scripts/agentcore_cli.py\" sources"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
