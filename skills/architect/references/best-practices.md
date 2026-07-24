# AgentCore Best Practices (per component)

Stable guidance distilled from AWS's published best-practice pages. For the authoritative, current version of any item, fetch the relevant doc — especially `runtime-security-best-practices`, `agentcore-vpc` (best-practices section), and `harness-security` in the developer guide.

## Runtime

- **Wrap, don't rewrite.** Existing framework code (Strands/LangGraph/CrewAI/ADK/OpenAI Agents) needs only the `BedrockAgentCoreApp` entrypoint wrapper — keep the migration diff minimal.
- **Enforce session-to-user mapping in your backend.** AgentCore isolates sessions in microVMs but does *not* enforce which user owns which session ID. Your backend must map users ↔ session IDs and cap sessions per user.
- **Assume everything in the microVM can read the execution role credentials** (metadata endpoint). Scope the execution role to the minimum: this is the blast radius if the agent is prompt-injected.
- **Use versioning + endpoints.** Point production clients at a named endpoint pinned to a tested version; roll forward by repointing the endpoint.
- **Stream responses** for interactive UX; use async patterns for long-running work rather than holding a synchronous connection.

## Harness

- Prefer Harness when the agent is expressible as config — model/tool/prompt changes become config updates, not redeploys.
- Set **execution limits** (`maxIterations`, `timeoutSeconds`, `maxTokens`, idle/lifetime) deliberately — they are the cost and runaway-loop guardrails.
- Use **export-to-code** as the escape hatch when you outgrow config; don't start with code "just in case."

## IAM / Security

- **Never ship CLI-generated IAM policies to production.** They are intentionally broad for dev. Write least-privilege policies scoped to specific resource ARNs.
- **Confused-deputy protection**: execution role trust policies must condition on `aws:SourceAccount` and `aws:SourceArn`.
- **Explicitly deny `InvokeAgentRuntimeForUser`** where user-id delegation isn't needed.
- **Privilege ceiling**: the execution role must have ≤ privileges of the principals allowed to invoke the runtime — otherwise invoking the agent is a privilege escalation.
- Cross-account access needs resource policies on **both** the runtime and the endpoint.
- Validate policies with IAM Access Analyzer.

## Identity

- Store third-party credentials in **credential providers / the token vault** — never in env vars, code, or container images.
- Use OAuth 3LO when downstream actions must carry the user's permissions; 2LO/API-key when the agent acts as itself. Getting this wrong is an audit finding, not a style choice.
- Reuse the org's existing IdP; don't stand up a new user pool if one exists.

## Gateway

- Front production Runtimes with a Gateway: single place for authN/Z, throttling, tool governance, and traffic observability.
- Name targets deliberately — tool names derive from target names and leak into prompts and Cedar policies.
- Use **outbound authorization** per target rather than one god-credential for all tools.
- Prefer built-in connectors/integration templates over hand-rolling SaaS clients (verify current catalog live).
- Use the semantic **tool search** feature when the tool count is large, instead of stuffing every tool schema into agent context (verify feature availability live).

## Memory

- Scope with **actor IDs per user from day one**; namespace design is a one-way door.
- Pick strategies by need, not "all of them": each strategy adds extraction cost. Semantic + summary is a sensible default; add user-preference/episodic when the UX calls for it.
- Memory is for interaction-derived context. Corpus retrieval belongs in a Knowledge Base (Gateway Managed-KB connector), not stuffed into memory.

## VPC / Networking

- ≥ 2 private subnets in different **supported** AZs (fetch the live AZ table; unsupported AZs fail at creation).
- A public subnet does **not** give the agent internet access — internet egress requires private subnets routing to a NAT gateway.
- Prefer VPC endpoints over NAT for AWS-service traffic (latency, reliability, cost).
- Put agent subnets in the same AZs as the resources they call (cross-AZ latency and transfer costs).
- Enable VPC Flow Logs; review for unexpected egress.
- ENIs are shared per subnet+SG combination and can persist up to ~8h after agent deletion — don't panic-delete.
- Enforce org-wide VPC usage with `bedrock-agentcore:subnets` / `securityGroups` IAM condition keys.

## Code Interpreter / Browser

- **Never execute model-generated code in the agent process** — always route through Code Interpreter's sandbox.
- Browser tool needs internet: in a VPC that means NAT. Treat browser sessions as untrusted-input surfaces (prompt injection via web content) — pair with Policy constraints on what tools the agent may call afterwards.

## Observability / Evaluations

- Turn on observability in every environment. Traces are how you debug agent loops; retrofitting after an incident is too late.
- Alarm on error rate, p95 latency, and token consumption (cost runaway detection).
- Wire Evaluations before launch for production agents; use scores as a regression gate in CI, not a dashboard ornament.

## Cost

- Consumption-based pricing means idle time is free but runaway loops are not — execution limits and token alarms are the cost controls.
- Always fetch current pricing from the FAQ source for estimates; show the formula (sessions/day × duration × resources), not just a number.

## Deployment

- PoC: AgentCore CLI (`agentcore create` → `dev` → `deploy` → `invoke`) is the fastest loop; it drives CDK under the hood.
- Production: explicit IaC (CDK/CloudFormation — verify current resource coverage live) in CI/CD, separate accounts or at least separate stacks per environment, `deploy --dry-run`/`cdk diff` gating.
- Tag everything (cost allocation + Policy conditions can use tags).
