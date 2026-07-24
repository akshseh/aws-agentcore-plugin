# Requirements Elicitation Checklist

How to use: don't run this as a survey. Classify the intent first (PoC vs. production vs. migration), ask the **Tier 1** questions, apply defaults for Tier 2 while stating them, and only open Tier 3 topics when a Tier 1/2 answer triggers them.

## Tier 1 — Always ask (blocks the design)

### 1. Posture: PoC or production?

- **PoC / demo**: optimize for time-to-running-agent. AgentCore CLI defaults, CLI-generated IAM (dev-only), no VPC unless private data is involved, single region. Explicitly list what must change before production.
- **Production**: full pass on security, networking, IaC, observability, quotas, and multi-environment strategy.
- If the user says "PoC now, production later": design the PoC but choose options that don't require teardown later — see "one-way doors" below.

### 2. Security & network boundary

Ask concretely, not abstractly:
- "Does the agent need to reach anything private — internal databases, internal APIs, private MCP servers, on-prem systems?" → **yes** ⇒ VPC connectivity for Runtime/tools and/or Gateway VPC egress.
- "Is there a compliance/security requirement that traffic to or from the agent never crosses the public internet?" → **yes** ⇒ PrivateLink interface endpoints for inbound API calls, VPC egress for outbound.
- "Any data-residency or region constraint?" → verify the region supports the needed AgentCore features **live** (search docs for "supported regions" and, if VPC is needed, the supported-AZ table — VPC attachment fails in unsupported AZs).
- If all answers are no: default to the public (non-VPC) configuration — it's the AgentCore default, simplest, and still runs each session in an isolated microVM.

### 3. Identity: who calls, and as whom does the agent act?

Two independent axes — never conflate them:

- **Inbound** (who invokes the agent): service-to-service → IAM SigV4 (default). End users through an app → OAuth/JWT via an IdP (Cognito, Okta, Entra ID, or a private IdP in a VPC). Ask which IdP already exists.
  ⚠️ Inbound auth mode has historically been immutable after resource creation on some resources — verify current behavior in the live docs, and treat it as a one-way door regardless.
- **Outbound** (how the agent authenticates to tools/APIs): agent's own identity → IAM execution role or API-key credential provider (2LO). On behalf of the end user → OAuth 3-legged flow via AgentCore Identity's token vault. Ask: "Should downstream systems see the *user's* permissions or the *agent's*?"

### 4. Existing setup to plug into

- Existing **VPC** (IDs, subnets, which AZs), existing **IdP**, existing **IaC** (CDK language? Terraform? CloudFormation? none?), existing **CI/CD**.
- Existing **agent code**: framework (Strands, LangGraph, CrewAI, Google ADK, OpenAI Agents SDK, plain Python) and where it runs today. Migration designs should minimize the code diff.
- **Org constraints**: SCPs, permission boundaries, mandatory tags, restricted regions, centralized networking account.
- Existing **tools/APIs** the agent must call: Lambda functions, REST APIs (OpenAPI spec available?), MCP servers, SaaS (Slack/Jira/Salesforce — Gateway has built-in integration templates; verify the current list live).

## Tier 2 — Default and state (ask only if signals conflict)

| Topic | Default | Override signal |
|---|---|---|
| Harness vs. Runtime | Harness for config-expressible agents (fastest, managed loop); Runtime when custom orchestration, framework choice, or bidirectional streaming is needed | Existing framework code ⇒ Runtime. "No code" / ops team ⇒ Harness |
| Framework (if Runtime) | Strands Agents (AWS-native, first-class SDK support) | Team already invested in LangGraph/CrewAI/ADK — keep it |
| Model provider | Amazon Bedrock | Existing provider contract (OpenAI/Gemini/Anthropic direct) |
| Memory | Short-term only for PoC; short + long-term for anything user-facing across sessions | Stateless one-shot tasks ⇒ none |
| Memory strategies | Semantic + summary; add user-preference for personalization; episodic for "recall what we did" flows | Verify current strategy list live |
| Build type | CodeZip (direct code deploy) — no container pipeline needed | Custom system deps / non-supported runtime ⇒ Container |
| IaC | Match what the org uses; else AgentCore CLI (CDK under the hood) for PoC, explicit CDK for production | — |
| Observability | Always on (CloudWatch/OTEL). Non-negotiable for production | — |
| Language | Python | Team is TypeScript-first (CLI supports it — verify current support) |

## Tier 3 — Conditional deep-dives

Open only when triggered:

- **Human-in-the-loop / approvals** (refunds, destructive actions) → interrupt patterns + Policy (Cedar) conditions.
- **Multi-agent** (>1 agent, A2A) → Runtime A2A protocol, Gateway as shared tool layer, Agent Registry.
- **Long-running / async work** (>ish minutes; verify current sync limits in docs) → async invocation patterns, lifecycle configuration.
- **Real-time voice/video** → bidirectional streaming (WebSocket/WebRTC) — Runtime only, not Harness.
- **Web automation** → Browser tool (needs NAT for internet if VPC-attached).
- **Generated-code execution** → Code Interpreter (never exec model output in the agent process).
- **Scale/quotas** → expected sessions/day, concurrency, payload sizes → check live quota pages; plan quota increases early for production.
- **Cost sensitivity** → fetch current pricing from the FAQ source; never quote prices from memory.
- **Multi-account** — cross-account memory access, resource policies, centralized gateway account.

## One-way doors (call these out whenever posture is "PoC now, production later")

1. **Inbound auth mode** on a resource (IAM vs. OAuth) — treat as fixed at creation; verify current mutability in docs.
2. **Region choice** — feature and AZ support varies; moving later means recreating resources.
3. **Memory organization** (actor/session namespace design) — retrofitting per-user scoping onto a shared memory store is painful.
4. **Gateway tool naming** — tool names derive from target names; renaming breaks agent prompts and policies.
5. **VPC AZ selection** — subnets must be in supported AZs; check the live table before creating anything.
