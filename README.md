# Amazon Bedrock AgentCore Assistant — an AI Coding Skill

A self-contained **skill** that gives any AI coding assistant that loads skills (Claude Code, Cursor, Kiro, and others) comprehensive, always-fresh knowledge about Amazon Bedrock AgentCore — AWS's managed platform for building, deploying, and operating AI agents.

Everything is a skill. There is no separate server to run, no ports, and **no packages to install** — the skill bundles a dependency-free Python CLI that fetches live documentation on demand, alongside curated best-practice guidance.

## Problem

AI coding assistants hallucinate when asked about AgentCore. They recommend EKS, Fargate, or patterns that don't exist because AgentCore is newer than their training data — they don't know its Runtime, Harness, Memory, Gateway, and other services. This skill fixes that by grounding every answer in official AWS documentation and layering on opinionated best-practice guidance.

## What's in the skill

```
skills/agentcore/
  SKILL.md                    # the skill: intent detection + 8 guided workflows
  scripts/
    agentcore_cli.py          # knowledge CLI: list | search | fetch | sources
    lib/
      sources.py              # 13 source definitions
      doc_index.py            # multi-source parser + search
      fetcher.py              # HTTP fetch, HTML→Markdown, on-disk TTL cache
  references/
    best-practices.md         # do-this guidance for every component
    anti-patterns.md          # avoid-this patterns + Top 10
```

### The knowledge CLI

The skill drives a small CLI. It uses only the Python standard library, so nothing needs installing or building, and it runs on macOS, Linux, and Windows.

```bash
python3 scripts/agentcore_cli.py list                                  # overview of all components
python3 scripts/agentcore_cli.py search "memory strategies" --source docs
python3 scripts/agentcore_cli.py fetch "https://docs.aws.amazon.com/.../memory.html"
python3 scripts/agentcore_cli.py sources                               # list enabled sources
```

> On **Windows**, use `python` (or the `py` launcher) in place of `python3` — e.g. `python scripts\agentcore_cli.py list`.

It indexes **1800+ pages across 13 live official AWS sources** with zero static content that can go stale:

| ID | Source | Content |
|----|--------|---------|
| `docs` | Developer Guide | Concepts, tutorials, getting started, configuration |
| `api_data_plane` | Data Plane API Reference | InvokeHarness, Memory CRUD, Browser, Code Interpreter, Identity tokens |
| `api_control_plane` | Control Plane API Reference | Create/Update/Delete for runtimes, gateways, harnesses, policies |
| `boto3_data_plane` | Boto3 Data Plane | Python client methods for runtime operations |
| `boto3_control_plane` | Boto3 Control Plane | Python client methods for resource management |
| `sdk` | AgentCore Python SDK | BedrockAgentCoreApp, MemoryClient, framework integrations |
| `cloudformation` | CloudFormation Reference | Resource types and properties for IaC |
| `cdk_typescript` | CDK TypeScript | L1 constructs with code examples |
| `cdk_python` | CDK Python | `aws_cdk.aws_bedrockagentcore` module |
| `cdk_java` | CDK Java | Java construct library |
| `cdk_dotnet` | CDK .NET | .NET construct library |
| `cdk_go` | CDK Go | Go construct library |
| `faq` | AWS FAQs | Pricing, regions, supported frameworks/models |

### The adaptive skill

`SKILL.md` decides *how* to answer. It detects intent and follows the matching workflow instead of dumping raw docs:

| You say | The skill does |
|---------|----------------|
| "What is AgentCore?" / "where do I start" | Guided onboarding — component overview + personalized learning path |
| "I have existing LangGraph/CrewAI code" | Migration assistant — before/after diff showing the minimal wrap |
| "how much does it cost?" | Cost estimation from the FAQ source, with consumption-vs-always-on comparison |
| "design / architect / what components" | Architecture recommendation with an ASCII diagram |
| "build me X" | Full implementation — architecture, code, IaC, deploy commands, verification |
| "are we production ready?" | Checklist with ✅/❌ across security, reliability, observability, quality |
| "why not EKS / Lambda / Bedrock Agents?" | Structured comparison table with honest trade-offs |

It grounds every answer in the CLI (no hallucinated APIs) and reads two curated reference files (`best-practices.md`, `anti-patterns.md`) when relevant.

## Install

Prerequisite: **Python 3.8+** — check with `python3 --version` (macOS/Linux) or `python --version` (Windows). Nothing else.

The skill is just the `skills/agentcore/` folder. Drop it into whatever directory your tool looks for skills in — you don't need the rest of the repo. Locations differ only by tool:

| Tool | Skills directory |
|------|------------------|
| Claude Code (project) | `<project>/.claude/skills/` |
| Claude Code (global) | `~/.claude/skills/` |
| Cursor | `<project>/.cursor/skills/` |
| Kiro | `<project>/.kiro/skills/` |
| Any other skill-loading assistant | that tool's skills dir |

Directory names vary between assistants and versions — check your tool's docs, then put the `agentcore` folder there.

### Quickest: pull only the skill folder into a project

This shallow **sparse** clone grabs *only* `skills/agentcore/` (not the whole repo). Set `SKILLS_DIR` for your tool, then run from your project root:

```bash
# .claude/skills (Claude Code), .cursor/skills (Cursor), .kiro/skills (Kiro), ...
SKILLS_DIR=.claude/skills

git clone --depth 1 --filter=blob:none --sparse \
  https://github.com/akshseh/aws-agentcore-plugin.git /tmp/agentcore-skill \
  && git -C /tmp/agentcore-skill sparse-checkout set skills/agentcore \
  && mkdir -p "$SKILLS_DIR" \
  && cp -R /tmp/agentcore-skill/skills/agentcore "$SKILLS_DIR/agentcore" \
  && rm -rf /tmp/agentcore-skill
```

Result: `<project>/<SKILLS_DIR>/agentcore`.

### With the bundled installer (Claude Code)

If you have the repo checked out, `install.sh` / `install.ps1` handle the Claude Code locations for you:

```bash
# macOS / Linux
./install.sh /path/to/your/project    # into one project → <project>/.claude/skills/agentcore
./install.sh --global                 # for all projects → ~/.claude/skills/agentcore
```

```powershell
# Windows (PowerShell)
.\install.ps1 C:\path\to\your\project  # into one project
.\install.ps1 -Global                  # for all projects
```

### Manually (any tool)

Copy the `skills/agentcore` directory into your tool's skills directory:

```bash
# macOS / Linux — replace .claude/skills with your tool's skills dir
cp -R skills/agentcore /path/to/project/.claude/skills/agentcore
```

```powershell
# Windows (PowerShell)
Copy-Item -Recurse skills\agentcore C:\path\to\project\.claude\skills\agentcore
```

See [INSTALLATION.md](INSTALLATION.md) for per-tool details and advanced configuration.

## Verify

Open your assistant in the project and ask:

```
What components does AgentCore have?
```

It should run `agentcore_cli.py list` and return a structured overview of all AgentCore services. You can also test the CLI directly:

```bash
# macOS / Linux
python3 skills/agentcore/scripts/agentcore_cli.py sources

# Windows (PowerShell)
python skills\agentcore\scripts\agentcore_cli.py sources
```

## Configuration

Set these environment variables (e.g. in your shell or a wrapper) to tune the CLI:

| Variable | Default | Description |
|----------|---------|-------------|
| `AGENTCORE_CACHE_TTL_MINUTES` | `60` | How long fetched pages stay cached (on disk, in the temp dir) |
| `AGENTCORE_SOURCES` | `all` | Which sources to enable |

Source selection:

```bash
AGENTCORE_SOURCES=all                              # all 13 sources (default)
AGENTCORE_SOURCES=docs,api_data_plane,faq          # specific sources only
AGENTCORE_SOURCES=-cdk_java,-cdk_dotnet,-cdk_go    # all except these
```

## License

Apache-2.0
