# Installation Guide

## Overview

The AgentCore Assistant is a **skill**. It bundles a dependency-free Python CLI that indexes 13 official AWS sources for Amazon Bedrock AgentCore and fetches them live on demand. Zero static content — everything is pulled dynamically and cached locally with a configurable TTL.

There is no server to run, no ports, and no packages to install. You only need **Python 3.8+**, which the skill's CLI uses for the actual documentation fetches. It runs on macOS, Linux, and Windows.

### Sources

| ID | Source | What it provides |
|----|--------|-----------------|
| `docs` | Developer Guide | Concepts, tutorials, getting started, configuration |
| `api_data_plane` | Data Plane API Reference | Operations for invoking agents, memory, browser, code interpreter |
| `api_control_plane` | Control Plane API Reference | CRUD operations for runtimes, gateways, harnesses, policies |
| `boto3_data_plane` | Boto3 Data Plane | Python client methods for runtime operations |
| `boto3_control_plane` | Boto3 Control Plane | Python client methods for resource management |
| `sdk` | AgentCore Python SDK | BedrockAgentCoreApp, MemoryClient, framework integrations |
| `cloudformation` | CloudFormation Reference | Resource types and properties for infrastructure-as-code |
| `cdk_typescript` | CDK TypeScript | L1 constructs with code examples |
| `cdk_python` | CDK Python | aws_cdk.aws_bedrockagentcore module |
| `cdk_java` | CDK Java | Java construct library |
| `cdk_dotnet` | CDK .NET | .NET construct library |
| `cdk_go` | CDK Go | Go construct library |
| `faq` | AWS FAQs | Pricing, regions, supported frameworks, capabilities |

---

## Installing across tools

**The skill is a single self-contained folder: `skills/agentcore/`.** Installing it into any tool is the same one move — put that folder wherever the tool looks for skills. You do not need the rest of this repo.

The install locations differ only by tool:

| Tool | Skills directory | Result path |
|------|------------------|-------------|
| **Claude Code** (project) | `<project>/.claude/skills/` | `<project>/.claude/skills/agentcore/` |
| **Claude Code** (global) | `~/.claude/skills/` | `~/.claude/skills/agentcore/` |
| **Cursor** | `<project>/.cursor/skills/` | `<project>/.cursor/skills/agentcore/` |
| **Kiro** | `<project>/.kiro/skills/` | `<project>/.kiro/skills/agentcore/` |
| **Other skill-loading assistant** | that tool's skills dir | `<skills-dir>/agentcore/` |

> Directory names differ between assistants and versions — check your tool's docs for where it discovers skills, then drop the `agentcore` folder there. On any tool, the runtime requirement is the same: Python 3.8+ on the machine.

### One command: pull only the skill folder into a project

This shallow **sparse** clone grabs *only* `skills/agentcore/` (not the whole repo) and copies it into your target directory. Set `SKILLS_DIR` to match your tool, then run from your project root:

```bash
# Set to your tool's skills dir: .claude/skills (Claude Code), .cursor/skills (Cursor), .kiro/skills (Kiro)
SKILLS_DIR=.claude/skills

git clone --depth 1 --filter=blob:none --sparse \
  https://github.com/akshseh/aws-agentcore-plugin.git /tmp/agentcore-skill \
  && git -C /tmp/agentcore-skill sparse-checkout set skills/agentcore \
  && mkdir -p "$SKILLS_DIR" \
  && cp -R /tmp/agentcore-skill/skills/agentcore "$SKILLS_DIR/agentcore" \
  && rm -rf /tmp/agentcore-skill

echo "Installed to $SKILLS_DIR/agentcore"
```

### With the bundled installer (Claude Code)

If you already have the repo checked out, `install.sh` / `install.ps1` handle the Claude Code locations for you:

```bash
# macOS / Linux
./install.sh /your/project      # into one project → <project>/.claude/skills/agentcore
./install.sh --global           # for all projects → ~/.claude/skills/agentcore
```

```powershell
# Windows (PowerShell)
.\install.ps1 C:\your\project    # into one project
.\install.ps1 -Global            # for all projects
```

### Manually (any tool)

```bash
# macOS / Linux — replace .claude/skills with your tool's skills dir
cp -R skills/agentcore /your/project/.claude/skills/agentcore
```

```powershell
# Windows (PowerShell)
Copy-Item -Recurse skills\agentcore C:\your\project\.claude\skills\agentcore
```

No build step — the skill is Markdown plus a Python CLI.

### Tools that can't load skills but can run commands

If your assistant can't discover local skills but can invoke shell commands, point it at the knowledge CLI directly (use `python` instead of `python3` on Windows):

```bash
python3 /path/to/agentcore/scripts/agentcore_cli.py list
python3 /path/to/agentcore/scripts/agentcore_cli.py search "CreateGateway parameters" --source api_control_plane
python3 /path/to/agentcore/scripts/agentcore_cli.py fetch "<url>"
```

---

## The knowledge CLI

| Command | Description |
|---------|-------------|
| `list [--source <id>] [--component <name>]` | Structured overview of all AgentCore components across enabled sources — what each does, page counts, and key sub-topics. Run first to learn terminology. |
| `search "<query>" [--source <id>] [--max <n>]` | Search across enabled sources by keyword. Prints up to 3 results with live content snippets, plus additional results as links. Filterable by source. |
| `fetch "<url>"` | Fetch the full content of any documentation page by URL. Returns complete Markdown including code examples, API schemas, and tables. Cached with TTL. |
| `sources` | List the enabled source IDs. |

### Usage flow

```
1. list                                       → Discover what exists
2. list --component memory                    → Deep-dive one component
3. search "CreateGateway" --source api_control_plane → Find the specific API page
4. fetch "<url>"                              → Get full API details
```

---

## Configuration

The CLI reads two environment variables. Export them in your shell (or profile) before launching your assistant.

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `AGENTCORE_CACHE_TTL_MINUTES` | `60` | How long fetched content stays cached, in minutes (on disk, in the temp dir) |
| `AGENTCORE_SOURCES` | `all` | Which documentation sources to load |

### Source selection

```bash
# All 13 sources (default)
AGENTCORE_SOURCES=all

# Only specific sources (comma-separated IDs)
AGENTCORE_SOURCES=docs,api_data_plane,api_control_plane,faq

# Exclude specific sources (prefix with -)
AGENTCORE_SOURCES=-cdk_java,-cdk_dotnet,-cdk_go
```

Available IDs: `docs`, `api_data_plane`, `api_control_plane`, `boto3_data_plane`, `boto3_control_plane`, `sdk`, `cloudformation`, `cdk_typescript`, `cdk_python`, `cdk_java`, `cdk_dotnet`, `cdk_go`, `faq`

---

## Verify Installation

```bash
# CLI runs and lists 13 sources (use 'python' on Windows)
python3 <skill-path>/scripts/agentcore_cli.py sources
```

Then ask your assistant: "What components does AgentCore have?" — it should run the CLI's `list` command and return a structured overview.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| CLI won't run | Verify `python3 --version` returns 3.8+ (on Windows use `python --version`; the command is `python`/`py`, not `python3`) |
| Empty search results | Check internet connectivity — all content is fetched from AWS |
| Slow first query | Normal — the index loads on first use (~3-5 seconds for 13 sources in parallel), then caches |
| Wrong source in results | Use `--source` to filter (e.g., `--source api_control_plane`) |
| Stale content | Lower `AGENTCORE_CACHE_TTL_MINUTES`, or delete the `agentcore-skill-cache` folder in your temp dir |
| Skill doesn't trigger | Confirm `SKILL.md` exists at `.claude/skills/agentcore/SKILL.md` (or `~/.claude/skills/agentcore` for global) |

---

## Example Prompts

Try these with your assistant after installing:

1. "What components does AgentCore have?"
2. "How do I create a gateway via the control plane API?"
3. "Show me the boto3 method for invoke_harness"
4. "What's the pricing model for AgentCore?"
5. "How do I deploy a LangGraph agent on Runtime?"
6. "What memory strategies are available?"
7. "Show me the CreateMemory API parameters"
8. "What CloudFormation resources exist for AgentCore?"
9. "Show me CDK TypeScript constructs for Runtime"
