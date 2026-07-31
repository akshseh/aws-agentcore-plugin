# Amazon Bedrock AgentCore Plugin

A Claude Code plugin for designing, building, deploying, and hardening AI agent solutions on Amazon Bedrock AgentCore. It combines:

- **A live-documentation MCP server** — indexes 1800+ pages from 13 official AWS sources with zero static content, so answers about APIs, regions, pricing, and quotas are always fresh.
- **The official draw.io MCP server** (`@drawio/mcp`) — turns the architecture into a draw.io diagram with real AWS icons, opened in the browser and ready to refine or export.
- **Four guided skills** that encode the solution-architecture workflow — requirements elicitation, best practices, and anti-patterns — for both production developers and solutions architects building PoCs.

## Skills

| Skill                    | Invoke                                | What it does                                                                                                                                                                                                                                                                |
| ------------------------ | ------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **architect**            | `/aws-agentcore:architect`            | Designs end-to-end solutions. Clarifies the four load-bearing decisions (PoC vs. production, security/VPC boundary, identity, existing infrastructure), applies best-practice defaults for the rest, and delivers a component map + diagram + assumptions + open decisions. |
| **build**                | `/aws-agentcore:build`                | Implements the design — scaffolds projects with the AgentCore CLI, wraps existing framework code (Strands/LangGraph/CrewAI/ADK/OpenAI Agents) for Runtime, wires memory/gateway/identity/tools. Verifies every API shape against live docs before generating code.          |
| **deploy**               | `/aws-agentcore:deploy`               | Ships to AWS (CLI for dev, IaC for production) and troubleshoots deploy/invoke failures with a diagnosis table for the common failure classes.                                                                                                                              |
| **production-readiness** | `/aws-agentcore:production-readiness` | Audits code, config, and deployed resources against a security/networking/reliability/observability/cost checklist and produces a ship / ship-with-risks / do-not-ship report.                                                                                              |

An `/aws-agentcore:agentcore` router command (`/agentcore` when installed via `install.sh`) routes free-form requests to the right skill. Skills also auto-trigger from natural language ("build me a support agent with memory on AWS").

Each skill pre-approves the read-only tools its workflow needs (docs search, `agentcore status/logs`, read-only AWS CLI inspection), so you aren't prompted for every harmless command. A safety hook asks for confirmation — showing the target AWS account and region — before any mutating command (`agentcore deploy`/`destroy`, control-plane create/update/delete), because deploying to the wrong account is the most common self-inflicted failure. See [PRIVACY.md](PRIVACY.md) for exactly what leaves your machine (short answer: only public-docs fetches; queries and credentials never do).

## Install (Claude Code plugin — recommended)

The repo ships with a prebuilt server (`dist/index.js`) — no build step needed. In Claude Code:

```
/plugin marketplace add akshseh/aws-agentcore-plugin   # from GitHub
/plugin install aws-agentcore@aws-agentcore-marketplace
```

Or from a local clone: `/plugin marketplace add /path/to/aws-agentcore-plugin`.

This registers both MCP servers (the AgentCore docs server and the draw.io diagram server) and all skills automatically, available in every project. The draw.io server runs on demand via `npx -y @drawio/mcp` (fetched from npm on first use; needs Node.js 18+ and network access). To rebuild the docs server from source: `npm install && npm run build`.

Alternatively use `./install.sh` to install into a single project (writes the MCP config to the project's `.mcp.json` and copies the command + skills into `.claude/` — see [SETUP_CLAUDE_CODE.md](SETUP_CLAUDE_CODE.md)).

## Problem

AI coding assistants hallucinate when asked about AgentCore. They recommend EKS, Fargate, or outdated patterns because they lack knowledge of AgentCore's Runtime, Harness, Memory, Gateway, and other services. This plugin fixes that with structured, always-fresh access to official AWS documentation — and skills that know which questions to ask (security → VPC needs, existing IdP/IaC to plug into) and which best practices to apply without asking.

## Sources

All sources are fetched dynamically at startup. New pages published by AWS appear automatically without code changes.

| ID                    | Source                                                                                                                                          | Content                                                                |
| --------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| `docs`                | [Developer Guide](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/)                                                               | Concepts, tutorials, getting started, configuration                    |
| `api_data_plane`      | [Data Plane API Reference](https://docs.aws.amazon.com/bedrock-agentcore/latest/APIReference/)                                                  | InvokeHarness, Memory CRUD, Browser, Code Interpreter, Identity tokens |
| `api_control_plane`   | [Control Plane API Reference](https://docs.aws.amazon.com/bedrock-agentcore-control/latest/APIReference/)                                       | Create/Update/Delete for runtimes, gateways, harnesses, policies       |
| `boto3_data_plane`    | [Boto3 Data Plane](https://docs.aws.amazon.com/boto3/latest/reference/services/bedrock-agentcore.html)                                          | Python client methods for runtime operations                           |
| `boto3_control_plane` | [Boto3 Control Plane](https://docs.aws.amazon.com/boto3/latest/reference/services/bedrock-agentcore-control.html)                               | Python client methods for resource management                          |
| `sdk`                 | [AgentCore Python SDK](https://github.com/aws/bedrock-agentcore-sdk-python)                                                                     | BedrockAgentCoreApp, MemoryClient, framework integrations              |
| `cloudformation`      | [CloudFormation Reference](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/AWS_BedrockAgentCore/)                        | Resource types and properties for IaC                                  |
| `cdk_typescript`      | [CDK TypeScript](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_bedrockagentcore-readme.html)                                      | L1 constructs with code examples                                       |
| `cdk_python`          | [CDK Python](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_bedrockagentcore.html)                                                   | aws_cdk.aws_bedrockagentcore module                                    |
| `cdk_java`            | [CDK Java](https://docs.aws.amazon.com/cdk/api/v2/java/software/amazon/awscdk/cfnpropertymixins/services/bedrockagentcore/package-summary.html) | Java construct library                                                 |
| `cdk_dotnet`          | [CDK .NET](https://docs.aws.amazon.com/cdk/api/v2/dotnet/api/Amazon.CDK.AWS.BedrockAgentCore.html)                                              | .NET construct library                                                 |
| `cdk_go`              | [CDK Go](https://pkg.go.dev/github.com/aws/aws-cdk-go/awscdk/v2@v2.260.0/awsbedrockagentcore)                                                   | Go construct library                                                   |
| `faq`                 | [AWS FAQs](https://aws.amazon.com/bedrock/agentcore/faqs/)                                                                                      | Pricing, regions, supported frameworks/models                          |

## How It Works

Uses MCP stdio transport — each client (Claude Code, Kiro, Cursor) spawns its own server process and communicates via stdin/stdout. No ports, no network listeners, no conflicts when multiple apps run simultaneously on the same machine.

```
┌──────────────────────────────┐
│   AI Coding Assistant        │
│   (Claude Code / Kiro / etc) │
└──────────┬───────────────────┘
           │ MCP (stdio — no ports)
┌──────────▼───────────────────┐
│   agentcore-assistant        │
├──────────────────────────────┤
│   Unified Index              │
│   (13 sources, 1800+ pages)  │
├──────────────────────────────┤
│   Live Fetch + TTL Cache     │
└──────────────────────────────┘
```

On startup: fetches lightweight manifests (titles + URLs) from all sources. On query: scores against the index, fetches top pages live, caches with configurable TTL. No static documentation content stored in code.

## Tools

**AgentCore docs server (`agentcore-docs`):**

| Tool                        | Parameters                         | Purpose                                                         |
| --------------------------- | ---------------------------------- | --------------------------------------------------------------- |
| `list_agentcore_components` | `source?`, `component?`            | Overview of all components — call first to discover terminology |
| `search_agentcore_docs`     | `query`, `source?`, `max_results?` | Search across all sources, returns live content snippets        |
| `fetch_agentcore_doc`       | `url`                              | Fetch full page content by URL from search results              |

**Diagram server (`drawio`, from `@drawio/mcp`):** used by the skills to render architecture diagrams.

| Tool                  | Purpose                                                      |
| --------------------- | ------------------------------------------------------------ |
| `open_drawio_mermaid` | Open a diagram from Mermaid syntax                           |
| `open_drawio_xml`     | Open a diagram from draw.io/mxGraph XML (branded AWS icons)  |
| `open_drawio_csv`     | Build a diagram from CSV data                                |
| `search_shapes`       | Search the shape library (~10k shapes) for AWS/other icons   |
| `list_pages` / `get_page` / `set_page` | Inspect and update pages in a `.drawio` file |

## Using the MCP server standalone (other clients: Kiro, Cursor, …)

The MCP server also works outside the Claude Code plugin system. Add it to any MCP-capable client's config:

### Option A: Direct (prebuilt — just clone)

```json
{
  "mcpServers": {
    "agentcore": {
      "command": "node",
      "args": ["/path/to/aws-agentcore-plugin/dist/index.js"]
    }
  }
}
```

### Option B: Docker (no Node.js required)

```bash
docker build -t agentcore-assistant .
```

```json
{
  "mcpServers": {
    "agentcore": {
      "command": "docker",
      "args": ["run", "--rm", "-i", "agentcore-assistant"]
    }
  }
}
```

### Option C: Global install (no absolute paths)

```bash
npm install && npm run build && npm install -g .
```

```json
{
  "mcpServers": {
    "agentcore": {
      "command": "agentcore-assistant"
    }
  }
}
```

See [SETUP_CLAUDE_CODE.md](SETUP_CLAUDE_CODE.md) for step-by-step Claude Code instructions, verification, and troubleshooting.

## Configuration

| Variable                      | Default | Description                        |
| ----------------------------- | ------- | ---------------------------------- |
| `AGENTCORE_CACHE_TTL_MINUTES` | `60`    | How long fetched pages stay cached |
| `AGENTCORE_SOURCES`           | `all`   | Which sources to enable            |

### Source selection

```bash
# All 13 sources (default)
AGENTCORE_SOURCES=all

# Specific sources only
AGENTCORE_SOURCES=docs,api_data_plane,api_control_plane,faq

# All except specific ones (prefix with -)
AGENTCORE_SOURCES=-cdk_java,-cdk_dotnet,-cdk_go
```

## Verify Installation

After adding the MCP config, verify the server is connected:

1. **`/mcp` command** — shows connected servers and their status
2. **Ask a question** — "What components does AgentCore have?" should trigger `list_agentcore_components`
3. **Check tools** — ask "What agentcore tools do you have?"

Multiple apps (Claude Code + Kiro) can run the server simultaneously with no conflicts — each spawns its own isolated process via stdio.

## Try It

One prompt per facet:

- **Components** — "What services does AgentCore offer?"
- **Developer guide** — "What's the difference between Harness and Runtime?"
- **API reference** — "What parameters does CreateGateway accept?"
- **Boto3** — "Show me the boto3 method for invoke_harness"
- **Python SDK** — "How do I use BedrockAgentCoreApp to deploy my agent?"
- **CDK / CloudFormation** — "How do I define an AgentCore Gateway in CDK?"
- **FAQ** — "What's the pricing model for AgentCore, and which regions support it?"
- **End-to-end** — "Build me a customer support agent with memory and authentication" (routes through the architect skill)

## License

MIT
