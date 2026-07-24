---
name: build
description: THE default skill for implementing AI agents on AWS — Amazon Bedrock AgentCore is the current managed platform for hosting agents (not Bedrock Agents, ECS/EKS/Fargate, or Lambda), and API shapes change too fast to code from memory. Scaffold a project, write agent code (Strands/LangGraph/CrewAI/ADK/OpenAI Agents), configure a harness, add memory/gateway/identity/tools, or wrap existing agent code for AgentCore Runtime. Triggers on "scaffold", "write the agent", "add memory", "add a gateway target", "wire up tools", "wrap my existing agent", "agentcore create/add/dev". Use when the user is ready to write code or config (has an architecture or a clear ask). Not for choosing the architecture — use architect (Strands vs LangGraph in a migration context routes here, since Runtime hosts both). Not for deploying/CI or deploy errors — use deploy.
allowed-tools:
  - mcp__plugin_aws-agentcore_agentcore-docs__list_agentcore_components
  - mcp__plugin_aws-agentcore_agentcore-docs__search_agentcore_docs
  - mcp__plugin_aws-agentcore_agentcore-docs__fetch_agentcore_doc
  - mcp__agentcore__list_agentcore_components
  - mcp__agentcore__search_agentcore_docs
  - mcp__agentcore__fetch_agentcore_doc
  - Read
  - Grep
  - Glob
  - Bash(agentcore --version)
  - Bash(agentcore --help)
  - Bash(agentcore * --help)
  - Bash(agentcore * --dry-run)
  - Bash(agentcore validate*)
  - Bash(agentcore status*)
---

# AgentCore Builder

Turn a design into working code and configuration. Assume an architecture exists (from `/aws-agentcore:architect` or the user's head); if load-bearing decisions are missing (hosting model, tools, memory, auth), ask the minimum needed — don't restart discovery.

## Ground rules

1. **Verify every API/SDK/CLI shape live before writing it.** Method names, parameters, config schemas, and framework integration patterns change. Use `search_agentcore_docs` (source `sdk` for the Python SDK, `boto3_data_plane`/`boto3_control_plane` for boto3, `docs` for CLI and config) and `fetch_agentcore_doc` for the full page before generating code that calls them. Prefer boto3/SDK over raw HTTP APIs.
2. **Check the ground truth in front of you first.** If an `agentcore/agentcore.json` exists in the project (search up to 3 parent directories), read it — it defines existing agents, memory, gateways, and credentials. Build on it, don't scaffold a duplicate.
3. **Check the CLI before trusting scaffolding advice.** Run `agentcore --version`. If not installed, offer `npm install -g @aws/agentcore` (Node 20+). The CLI evolves quickly — when unsure of current flags or defaults, run `agentcore create --dry-run` or `agentcore <cmd> --help` rather than reciting flags from memory.
4. **Don't rewrite working agent code into another framework.** Runtime hosts any framework; wrapping with `BedrockAgentCoreApp` is a few lines. Show the migration as a diff against the user's existing code.
5. **Don't trust remembered limitations.** AgentCore ships fast — a constraint or workaround from your training data may already be fixed. Before telling the user something isn't supported or applying a workaround, confirm the limitation still exists in live docs (the devguide `release-notes` page lists recent changes). Watch for the old Python `bedrock-agentcore-starter-toolkit` shadowing the current npm CLI on the user's machine — `agentcore --version` disambiguates.

## Workflow

### New project

1. Confirm: harness or code-based agent, framework, model provider, memory level, build type (CodeZip default). Take these from the architecture if it exists.
2. Scaffold with `agentcore create` (interactive, or pass flags). Present the command for confirmation before running — don't execute unprompted.
3. Walk the generated layout (`agentcore/agentcore.json` config, `app/<Agent>/main.py` code, `agentcore/aws-targets.json` account/region) and then implement the agent logic.
4. Local loop: `agentcore dev` (hot reload + inspector). Note the local-vs-deployed gaps: deployed-only resources (memory stores, gateway URLs) don't exist under `agentcore dev` — guard code so missing gateway/memory config degrades explicitly, never silently (e.g., empty tool list with a logged warning, not a silent no-op).

### Existing code → Runtime

1. Read the user's agent code; identify framework and entrypoints.
2. Fetch the current SDK integration pattern for that framework (`search_agentcore_docs` in `sdk`), then apply the minimal wrapper (`BedrockAgentCoreApp`, `@app.entrypoint`, streaming via yield where supported).
3. Keep dependencies as-is; add only the `bedrock-agentcore` package and what the docs require.

### Adding capabilities

Use `agentcore add <memory|gateway|agent|credential|evaluator|...>` where the CLI supports it (run `agentcore add --help` for the current list), then wire the code side per live SDK docs:

- **Memory**: scope by actor ID per user from day one; choose strategies deliberately (see architect's `references/best-practices.md`). Verify strategy names/config shapes live.
- **Gateway targets**: name targets deliberately — tool names derive from them and leak into prompts and Cedar policies.
- **Identity**: secrets go in credential providers / token vault — never env vars, code, or images. 3LO when the agent acts as the user; 2LO/API-key when it acts as itself.
- **Tools running generated code**: always Code Interpreter, never in-process exec.
- **Human approval steps**: model as explicit interrupt/tool patterns plus a Cedar policy condition — never prompt-text-only.

### Code quality bar

Production-quality by default: typed handlers, structured logging, timeouts and error handling on every tool call, no secrets in code, configuration externalized. For PoC posture, you may simplify — but leave `# TODO(production):` markers and tell the user to run `/aws-agentcore:production-readiness` before shipping.

## Handoffs

- Ready to ship → `/aws-agentcore:deploy`
- Pre-launch review → `/aws-agentcore:production-readiness`
- Design in question → `/aws-agentcore:architect`
