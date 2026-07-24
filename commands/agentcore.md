---
description: AgentCore entry point — routes your request to the right skill (architect, build, deploy, production-readiness) or answers directly from live AWS docs
argument-hint: "[what you want to do — e.g. 'design a support agent with memory', 'deploy fails with AccessDenied', 'are we production ready?']"
---

The user asked: "$ARGUMENTS"

Route to the right capability:

1. **No arguments / "what is AgentCore" / comparisons / pricing / capability questions** → answer directly using the `agentcore-docs` MCP tools (`list_agentcore_components` first, then `search_agentcore_docs`, `fetch_agentcore_doc`). Never answer pricing/regions/quotas from memory.
2. **Design, architecture, "build me X", "which components", migration evaluation** → invoke the `aws-agentcore:architect` skill.
3. **Writing code/config, scaffolding, adding memory/gateway/tools, wrapping existing code** → invoke the `aws-agentcore:build` skill.
4. **Deploying, CI/CD, IaC, or any deploy/invoke error** → invoke the `aws-agentcore:deploy` skill.
5. **Production readiness, hardening, security review, PoC→prod promotion** → invoke the `aws-agentcore:production-readiness` skill.

If the request spans phases (e.g., "build me a customer support agent end to end"), start with architect and follow its handoffs.
