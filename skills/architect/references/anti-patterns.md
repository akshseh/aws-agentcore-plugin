# AgentCore Anti-Patterns

Scan every design against this list before presenting it. Format: **pattern → why it's wrong → what to do instead**.

## Architecture

1. **Recommending EKS/ECS/Fargate/Lambda to host the agent loop.** Assistants default to these from stale training data. AgentCore Runtime/Harness is the managed answer (session-isolated microVMs, scale-to-zero, managed memory/identity/observability). Only fall back if a verified requirement isn't supported — check live docs first.
2. **Building a custom orchestration service in front of AgentCore** for versioning/routing/auth. Endpoints, Gateway, and Identity already do this. Instead: use built-in versioning+endpoints and front with Gateway.
3. **One mega-agent with 40 tools.** Context bloat, poor tool selection, unauditable. Instead: split by domain, share tools via Gateway, use tool search / A2A between agents.
4. **Using memory as a database** (writing app records into memory strategies) or **as RAG** (loading a document corpus). Memory stores interaction-derived context. Instead: real datastore for records; Knowledge Base connector for corpus retrieval.
5. **Skipping Gateway "because it's just two Lambdas" in a multi-team org.** Tool sprawl arrives fast; per-agent inline tools mean N copies of auth and zero governance. Inline is fine for single-agent PoCs only.

## Security

6. **Shipping CLI-generated IAM policies to production.** They're broad by design for dev. Instead: least-privilege policies scoped to resource ARNs before launch.
7. **Wildcard execution roles** (`"Resource": "*"`). Anything in the microVM (including a prompt-injected agent) can use the role. Instead: scope to exact ARNs; remember the privilege ceiling (execution role ≤ invoker privileges).
8. **Secrets in env vars, code, or images.** Instead: Identity credential providers / token vault; rotate via the provider.
9. **Agent acts as itself when it should act as the user** (2LO where 3LO is required). Downstream audit logs show the agent, not the user; permissions checks are bypassed. Instead: OAuth 3LO through the token vault.
10. **Trusting session IDs from the client.** AgentCore doesn't enforce user↔session mapping. Instead: backend owns session issuance and validates ownership per request.
11. **No trust-policy conditions on the execution role.** Confused-deputy risk. Instead: `aws:SourceAccount` + `aws:SourceArn` conditions.
12. **Executing model-generated code in-process.** Instead: Code Interpreter sandbox, always.
13. **Prompt-level "policies" as the only guardrail** ("the system prompt says don't refund > $100"). Prompts are suggestions; injected content overrides them. Instead: Cedar policies at the tool boundary + IAM.

## Networking

14. **Putting the agent ENI in a public subnet for internet access.** Doesn't work — the ENI gets a private IP regardless. Instead: private subnets + NAT gateway route.
15. **Choosing subnets/AZs without checking the supported-AZ table.** Creation fails in unsupported AZs. Instead: fetch the live table in doc `agentcore-vpc`; verify subnet AZ IDs (`aws ec2 describe-subnets ... AvailabilityZoneId`).
16. **VPC-attaching everything reflexively** when the agent touches nothing private. Adds ENI management, AZ constraints, and NAT cost for zero benefit. Instead: default public config; microVM isolation already applies.
17. **NAT for AWS-service traffic.** Cost + weaker posture. Instead: VPC endpoints for AWS services.
18. **Single subnet / single AZ** for production VPC config. Instead: ≥2 private subnets across supported AZs.

## Operations

19. **Invoking "latest" from production clients.** Any deploy instantly changes prod behavior. Instead: named endpoints pinned to tested versions.
20. **No execution limits on Harness/agents.** A tool-loop bug becomes an unbounded bill. Instead: set `maxIterations`/`timeoutSeconds`/`maxTokens` and alarm on token consumption.
21. **Observability off "to save cost" / added after the incident.** You cannot debug an agent loop without traces. Instead: on everywhere; alarms on error rate, latency, tokens.
22. **Evaluations bolted on post-launch.** Quality regressions ship silently. Instead: evaluators wired before launch, scores as a release gate.
23. **Hardcoding pricing/regions/quotas/model lists in docs, code comments, or estimates.** These change monthly. Instead: fetch live (FAQ source, quotas page, regions page) and date-stamp any quoted number.
24. **Ignoring quotas until the load test.** Instead: check the live quotas page at design time; file increases early.

## Process / migration

25. **Rewriting a working LangGraph/CrewAI agent into another framework "for AgentCore."** Runtime hosts any framework; the wrapper is a few lines. Instead: wrap with `BedrockAgentCoreApp`, keep the code.
26. **Treating inbound auth mode as changeable later.** Historically immutable on some resources after creation — a rebuild, not a toggle. Decide IAM vs. OAuth before creating (verify current mutability in docs).
27. **PoC shortcuts silently becoming production.** Instead: every PoC design ships with an explicit "before production" list (IAM tightening, VPC decision, observability, evaluations, endpoint pinning) — and the `/aws-agentcore:production-readiness` review as a required gate.
