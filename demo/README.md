# Demo Scenarios

5 story-driven demos, each with continuity between prompts. Covers three personas at different depths.

## How to run

1. Open Claude Code in a project with the AgentCore Assistant MCP connected
2. Pick a demo folder
3. Feed prompts from `PROMPT.md` sequentially — each builds on the previous answer

---

## Demos

| # | Story | Persona | Prompts | Time |
|---|-------|---------|---------|------|
| 01 | [CTO Discovery](./01-cto-discovery/) | CTO evaluating options | 3 | 5-10 min |
| 02 | [Build and Ship](./02-techlead-build-and-ship/) | Tech lead building from requirements to production | 5 | 20-30 min |
| 03 | [Junior Dev Journey](./03-junior-dev-journey/) | Junior dev learning from zero | 4 | 15-20 min |
| 04 | [Migration Story](./04-migration-story/) | Engineering lead migrating from EKS | 3 | 15-20 min |
| 05 | [Platform at Scale](./05-platform-at-scale/) | Tech lead designing for 4 teams | 4 | 20-25 min |

---

## Quick picks

| Time available | Recommendation |
|----------------|----------------|
| **5 min** | Demo 01 (CTO discovery) — prompt 1 only |
| **10 min** | Demo 03 (junior dev) — prompts 1+2 |
| **20 min** | Demo 02 (build and ship) — prompts 1-3 |
| **30 min** | Demo 04 (migration) — full story |
| **Full showcase** | Demo 01 → 02 → 03 (shows all personas) |

---

## What each demo covers

| Capability | Demo |
|-----------|------|
| Component discovery | 01, 03 |
| Cost estimation | 01 |
| Compare alternatives | 01 |
| Architecture diagrams | 02, 05 |
| Full code generation | 02, 04 |
| CDK infrastructure | 02 |
| Gateway + Cedar policies | 02, 05 |
| Production checklist | 02 |
| Framework translation | 04 |
| Memory integration | 03, 04 |
| Tool addition | 03, 04 |
| Troubleshooting | 03 |
| Multi-agent design | 05 |
| Security review | 05 |
| Observability + evaluations | 04, 05 |
