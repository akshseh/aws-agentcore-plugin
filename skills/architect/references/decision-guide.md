# Component Decision Guide

Decision trees for mapping requirements → AgentCore components. These encode *stable* architectural logic; for anything volatile (feature support matrices, regions, quotas, pricing, API shapes), verify with `search_agentcore_docs` / `fetch_agentcore_doc` before committing. The doc `harness-vs-runtime` in the developer guide has the authoritative feature grid — fetch it when the choice is close.

## 1. Hosting: Harness vs. Runtime

```
Does the team have existing agent code (LangGraph, CrewAI, custom loop)?
├─ Yes → Runtime (wrap with BedrockAgentCoreApp; minimal diff)
└─ No
   Does the agent need any of: choice of framework, bidirectional streaming
   (voice/video), non-loop orchestration (graphs/workflows), custom hooks?
   ├─ Yes → Runtime
   └─ No → Harness (managed loop, config-only: model, prompt, tools,
            memory, limits are config fields; model/tool changes need no
            redeploy; can export to Strands code later if you outgrow it)
```

- Harness runs *on* Runtime — it's not a separate infrastructure tier. Choosing Harness first is not a dead end: `export to code` generates equivalent Strands source.
- Both support: VPC, session isolation, inbound IAM/OAuth, versioning/endpoints, EFS/S3 filesystems, env vars.

## 2. Tools connectivity: inline vs. Gateway

```
How many tools / targets, and who governs them?
├─ 1–2 simple tools, single agent, PoC → inline tools in agent code (or
│    harness inline tool config). Simplest; no extra resource.
└─ Any of: multiple agents sharing tools, REST/OpenAPI/Smithy targets,
   Lambda targets, external MCP servers, SaaS integrations, per-tool
   auth, central governance/audit of tool traffic
   → Gateway
      ├─ Lambda target        — existing Lambda functions as tools
      ├─ OpenAPI target       — REST APIs with a spec
      ├─ API Gateway target   — existing API Gateway stages
      ├─ Smithy target        — Smithy-modeled services
      ├─ MCP server target    — aggregate external MCP servers
      ├─ HTTP passthrough     — direct routing, no aggregation
      ├─ Inference targets    — route LLM traffic through the gateway
      └─ Built-in connectors / integration templates (Slack, Jira,
         Salesforce, Managed KB, Web Search — verify current list live)
```

- Gateway is also the recommended *front door* for a Runtime in production (auth, throttling, observability at the boundary).
- Tool names derive from target names — pick target names deliberately (renames break prompts/policies).

## 3. Memory

```
Does the agent need context beyond a single invocation?
├─ No (stateless task agent) → no Memory resource
└─ Yes
   Within one session only? → short-term memory
   Across sessions / personalization?
   → long-term with strategies:
      ├─ semantic         — facts ("customer's plan is Pro")
      ├─ summary          — condensed session narratives
      ├─ user-preference  — styles/choices ("prefers terse replies")
      └─ episodic        — "what happened when we did X" recall
   (Custom/self-managed strategies exist for domain-specific extraction —
    check docs when defaults don't fit.)
```

- Scope memory per user with actor IDs from day one (retrofit is painful).
- Memory ≠ RAG: long-term memory stores interaction-derived context; for a document corpus use a Knowledge Base (Gateway has a Managed KB connector). The doc `memory-ltm-rag` covers the distinction.

## 4. Identity

**Inbound (who can invoke):**
```
Caller is a service/backend inside AWS → IAM SigV4 (default)
Caller is an end-user app → OAuth/JWT: point at existing IdP
  (Cognito / Okta / Entra / any OIDC; private IdPs in a VPC are supported
   via the private-IdP feature — verify setup in docs)
```
⚠️ Treat inbound auth mode as fixed at resource creation (one-way door).

**Outbound (how the agent reaches tools):**
```
Downstream must see the USER's permissions → OAuth 3LO via Identity
  token vault (user consents once; tokens stored/refreshed by AgentCore)
Downstream sees the AGENT's identity →
  ├─ AWS services → execution role (least-privilege, scoped ARNs)
  └─ External APIs → API-key or OAuth 2LO credential provider
```

Never put secrets in env vars or code — that's what the token vault / credential providers are for.

## 5. Network

```
Agent (or its tools) needs to reach private resources
(RDS, internal APIs, private MCP servers, on-prem)?
├─ No → default public config. Sessions still run in isolated microVMs;
│        no VPC needed. Simplest and cheapest.
└─ Yes → VPC attachment
   ├─ Runtime / Code Interpreter / Browser → VPC config on the resource
   │   (ENIs created in your subnets via service-linked role)
   ├─ Gateway targets in a VPC → Gateway VPC egress (VPC Lattice)
   ├─ ≥2 private subnets in different SUPPORTED AZs (fetch the live AZ
   │   table from doc `agentcore-vpc` — unsupported AZ ⇒ creation fails)
   ├─ Internet from inside the VPC (e.g., Browser tool, public APIs)
   │   → NAT gateway in a public subnet; a public subnet alone does NOT
   │     give the ENI internet access
   └─ Prefer VPC endpoints over NAT for AWS services (cost + security)

Callers must reach the AgentCore APIs privately (no internet traversal)?
└─ Yes → PrivateLink interface endpoints in the caller's VPC
```

Enforcement: for orgs mandating VPC, use IAM condition keys (`bedrock-agentcore:subnets`, `bedrock-agentcore:securityGroups`) to deny non-VPC deployments.

## 6. Cross-cutting

- **Observability**: enable for every environment. OTEL traces/metrics/logs → CloudWatch. For production, add alarms on error rate, latency, and token/cost metrics.
- **Policy (Cedar)**: use when tool calls need conditions beyond IAM ("only call refund tool if amount ≤ 100", "only query orders the user owns"). Policies attach at the gateway/tool boundary.
- **Evaluations**: built-in evaluators score quality continuously — wire in before launch for production agents, not after the first regression.
- **Versioning/endpoints**: use endpoints (e.g., `prod`, `staging`) pointing at pinned versions; never invoke "latest" from production clients.
- **Quotas**: fetch the live quotas page during design for production; request increases early.

## 7. Compare-with-alternatives cheat sheet (for "why not X?" conversations)

| Concern | EKS/ECS self-hosted | Lambda + Step Functions | AgentCore |
|---|---|---|---|
| Session isolation | DIY (containers share kernel) | per-invocation, but state is DIY | per-session microVM, managed |
| Scale-to-zero | No (nodes run 24/7) | Yes | Yes |
| Long-running sessions | Yes but you manage it | Hard timeout limits | Managed (verify current session limits live) |
| Agent memory | DIY | DIY | Managed service |
| Tool auth (OAuth vaulting) | DIY | DIY | Identity token vault |
| Ops burden | High | Medium | Low |

Use live FAQ/pricing data for any cost comparison — never invent numbers.
