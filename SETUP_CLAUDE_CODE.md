# Setup Guide: AgentCore Plugin with Claude Code

Everything you need to install, verify, and use the AgentCore plugin in Claude Code.

---

## Prerequisites

- **Node.js 18+** — check with `node --version`
- **Claude Code** — installed and working (`claude` command available)
- **Internet access** — the server fetches documentation live from AWS

---

## Step 1: Get the plugin

```bash
git clone https://github.com/akshseh/aws-agentcore-plugin.git
```

The repo ships with a prebuilt `dist/index.js` — the self-contained MCP server (bundled, no node_modules needed at runtime). To rebuild from source: `npm install && npm run build`.

---

## Step 2: Install

### Option A: Install as a plugin (recommended)

Inside Claude Code:

```
/plugin marketplace add /path/to/aws-agentcore-plugin
/plugin install aws-agentcore@aws-agentcore-marketplace
```

Or from the shell:

```bash
claude plugin marketplace add ./aws-agentcore-plugin
claude plugin install aws-agentcore@aws-agentcore-marketplace
```

This registers everything at once, available in all projects:
- the `agentcore-docs` MCP server (3 tools)
- the `drawio` MCP server (`@drawio/mcp`) for architecture diagrams
- skills: `/aws-agentcore:architect`, `/aws-agentcore:build`, `/aws-agentcore:deploy`, `/aws-agentcore:production-readiness`
- the `/aws-agentcore:agentcore` router command

If the plugin is hosted on GitHub, `/plugin marketplace add owner/repo` works directly.

### Option B: Per-project install script

```bash
cd /your/project
/path/to/aws-agentcore-plugin/install.sh
```

This writes the MCP config to `.mcp.json` at your project root and copies the command and skills into `.claude/`. Claude Code will ask you to approve the project MCP server on next launch.

### Option C: Manual setup

Create `.mcp.json` at your project root (note: MCP servers go in `.mcp.json`, **not** `.claude/settings.json`):

```json
{
  "mcpServers": {
    "agentcore": {
      "command": "node",
      "args": ["/path/to/aws-agentcore-plugin/dist/index.js"]
    },
    "drawio": {
      "command": "npx",
      "args": ["-y", "@drawio/mcp"]
    }
  }
}
```

Or equivalently:

```bash
claude mcp add agentcore --scope project -- node /path/to/aws-agentcore-plugin/dist/index.js
claude mcp add drawio --scope project -- npx -y @drawio/mcp
```

Copy the command and skills:

```bash
mkdir -p .claude/commands .claude/skills
cp /path/to/aws-agentcore-plugin/commands/agentcore.md .claude/commands/agentcore.md
cp -r /path/to/aws-agentcore-plugin/skills/. .claude/skills/
```

---

## Step 3: Verify it works

Open Claude Code in your project directory:

```bash
cd /your/project
claude
```

### Check 1: MCP is connected

Type `/mcp` — you should see two servers connected. The docs server is named `agentcore-docs` with the plugin install (`agentcore` with the per-project install):

```
agentcore-docs: connected (3 tools)
  - list_agentcore_components
  - search_agentcore_docs
  - fetch_agentcore_doc
drawio: connected
  - open_drawio_mermaid, open_drawio_xml, open_drawio_csv,
    search_shapes, list_pages, get_page, set_page
```

The `drawio` server is fetched from npm on first use (`npx -y @drawio/mcp`), so its first connection may take a few seconds.

### Check 2: Skill is available

Type `/` and look for `agentcore` in the autocomplete list.

### Check 3: End-to-end test

Ask Claude:

```
What components does AgentCore have?
```

You should see Claude call `list_agentcore_components` and return a structured overview of all AgentCore services.

---

## Step 4: Use it

### With the slash command

```
/aws-agentcore:agentcore Build me a customer support agent with memory and authentication
```

(With the per-project install it's just `/agentcore ...`.)

### Without the slash command (tools activate automatically)

Just ask naturally — Claude will use the MCP tools whenever you mention agents, AWS, deployment, memory, gateway, etc:

```
How do I deploy a LangGraph agent serverlessly on AWS?
```

---

## What you get

### MCP tools (always available)

Docs server (`agentcore-docs`):

| Tool | What it does |
|------|-------------|
| `list_agentcore_components` | Shows all AgentCore services and sub-topics |
| `search_agentcore_docs` | Searches 1800+ pages across 13 official sources |
| `fetch_agentcore_doc` | Fetches full page content by URL |

Diagram server (`drawio`):

| Tool | What it does |
|------|-------------|
| `open_drawio_mermaid` / `open_drawio_xml` / `open_drawio_csv` | Open a diagram from Mermaid, mxGraph XML, or CSV |
| `search_shapes` | Find AWS/other icons in the shape library |
| `list_pages` / `get_page` / `set_page` | Inspect and update pages in a `.drawio` file |

### 4 skills + a router command

| Skill | What it does |
|-------|-------------|
| `architect` | Requirements → architecture with component map, diagram, assumptions |
| `build` | Scaffold projects, wrap existing framework code, wire memory/gateway/identity |
| `deploy` | Ship via CLI or IaC; troubleshoot deploy/invoke failures |
| `production-readiness` | Security/networking/reliability/cost audit with ship / do-not-ship verdict |

The `/aws-agentcore:agentcore` command (`/agentcore` with per-project install) routes free-form requests to the right skill:

| You say | It does |
|---------|---------|
| "What is AgentCore?" / "How much does it cost?" | Answers directly from live docs |
| "Build me X" | architect → build → deploy handoff chain |
| "Deploy fails with AccessDenied" | deploy skill's troubleshooting table |
| "Are we production ready?" | production-readiness checklist with ✅/❌ and fixes |

### Reference files (used by the architect skill automatically)

| File | Content |
|------|---------|
| `requirements.md` | The elicitation checklist — what to ask vs. what to default |
| `decision-guide.md` | Component decision trees (Harness vs. Runtime, Gateway, memory, network) |
| `best-practices.md` | Do-this guidance for every AgentCore component |
| `anti-patterns.md` | Avoid-this patterns with explanations and fixes |

---

## Configuration (optional)

Set environment variables in your `.mcp.json` (per-project install) or in the plugin's bundled `.mcp.json` (plugin install):

```json
{
  "mcpServers": {
    "agentcore": {
      "command": "node",
      "args": ["/path/to/aws-agentcore-plugin/dist/index.js"],
      "env": {
        "AGENTCORE_CACHE_TTL_MINUTES": "30",
        "AGENTCORE_SOURCES": "docs,api_data_plane,api_control_plane,faq"
      }
    }
  }
}
```

| Variable | Default | Options |
|----------|---------|---------|
| `AGENTCORE_CACHE_TTL_MINUTES` | `60` | Any number (minutes) |
| `AGENTCORE_SOURCES` | `all` | Comma-separated: `docs`, `api_data_plane`, `api_control_plane`, `boto3_data_plane`, `boto3_control_plane`, `sdk`, `cloudformation`, `cdk_typescript`, `cdk_python`, `cdk_java`, `cdk_dotnet`, `cdk_go`, `faq` |

The `drawio` server reads one variable (set it in that server's `env` block):

| Variable | Default | Options |
|----------|---------|---------|
| `DRAWIO_BASE_URL` | `https://app.diagrams.net/` | URL of the draw.io editor. Point at a self-hosted instance to keep diagram content off the public editor. |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `/mcp` shows agentcore as disconnected | Check the path in `.mcp.json`. Run `node /path/to/dist/index.js` manually to see errors. |
| MCP server missing entirely | MCP servers must be in `.mcp.json` at the project root, not `.claude/settings.json`. Also check you approved the project server when Claude Code prompted (`claude mcp list` to inspect). |
| `/agentcore` doesn't appear as a command | Plugin install: it's namespaced — type `/aws-agentcore:agentcore`. Per-project install: ensure `.claude/commands/agentcore.md` exists. |
| `/mcp` shows drawio as disconnected | It runs via `npx -y @drawio/mcp`, so the first start downloads the package — needs `npx` on `PATH`, Node.js 18+, and network access. Run `npx -y @drawio/mcp --version` manually to see errors. |
| "Failed to load index" error | Check internet connectivity. The server needs to reach docs.aws.amazon.com. |
| Slow first response | Normal — the index loads on first use (~3-5 seconds). Subsequent queries are fast. |
| Stale documentation | Restart Claude Code (the server restarts and reloads fresh). Or set a lower cache TTL. |
| Works in one project but not another | Per-project installs (`install.sh` / `.mcp.json`) apply to one project. Install the plugin (Option A) for all projects. |

---

## Uninstall

Plugin install:

```
/plugin uninstall aws-agentcore@aws-agentcore-marketplace
```

Per-project install — remove the `agentcore` entry from `.mcp.json` (delete the file only if it contains nothing else), then:

```bash
rm .claude/commands/agentcore.md
rm -rf .claude/skills/architect .claude/skills/build .claude/skills/deploy .claude/skills/production-readiness
```

Or if globally installed:

```bash
npm uninstall -g agentcore-assistant
```
