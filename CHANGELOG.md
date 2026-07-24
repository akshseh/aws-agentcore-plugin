# Changelog

## 4.3.0 — 2026-07-24

- **Organic skill engagement**: architect and build skill descriptions now identify themselves as the default path for any agent-shaped request on AWS (AI assistants, chatbots, autonomous AI workflows, serverless hosting for LangGraph/CrewAI/Strands apps, central MCP/tool management for coding assistants) and warn that training-data AWS agent patterns are stale. Verified against 7 naive-user scenarios drawn from awslabs/agentcore-samples: organic engagement went from 3/7 to 7/7, and engaged designs matched the official sample architectures.
- **Fix**: removed the explicit `hooks` key from plugin.json — Claude Code ≥2.1.x auto-loads `hooks/hooks.json`, and declaring it twice made the plugin fail to load.
- **Fix**: production-readiness skill frontmatter contained an unquoted `Read-only:` colon that broke YAML parsing, silently dropping all frontmatter (including allowed-tools) at runtime. Caught by `claude plugin validate --strict`.
- **Fix**: MCP tool descriptions in `src/index.ts` still referenced the old 6-source layout and a 500+ page count; updated to the current 13 sources / 1800+ pages.

## 4.2.0 — 2026-07-23

- Per-skill `allowed-tools` pre-approving read-only docs/CLI tools.
- PreToolUse safety hook: shows target AWS account/ARN/region and asks before mutating commands (`agentcore deploy`/`destroy`, control-plane create/update/delete).
- Trigger phrases, negative routing, and tie-breakers in all skill descriptions; stale-knowledge ground rule (verify remembered limitations against live release notes).
- GitHub Actions CI (structure validation, build freshness, tests) and `scripts/validate-plugin.mjs`.
- PRIVACY.md documenting exactly what leaves the machine.

## 4.1.0 — 2026-07-23

- Ship-ready repo: MIT license alignment, unified versioning, `install.sh` writing project MCP config to `.mcp.json`, unscoped npm name, Node .gitignore keeping `dist/index.js` tracked.

## 4.0.0 — 2026-07-23

- Initial plugin packaging: live-documentation MCP server (13 AWS sources, zero static content), four guided skills (architect, build, deploy, production-readiness) with reference files, router command, local marketplace.
