---
name: production-readiness
description: Review an AgentCore agent/solution against production best practices and produce a pass/fail report with fixes — security (IAM, secrets, session handling), networking, reliability, observability, evaluations, cost controls, and operations. Triggers on "production ready", "harden", "security review", "pre-launch review", "audit my agent", "go-live checklist", or a PoC being promoted to production. Read-only — findings hand off to build (code/config fixes) and deploy (redeploy). Not for designing new architecture — use architect. Not for diagnosing active failures — use deploy.
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
  - Bash(aws sts get-caller-identity*)
  - Bash(aws bedrock-agentcore-control list-*)
  - Bash(aws bedrock-agentcore-control get-*)
  - Bash(aws iam get-role*)
  - Bash(aws iam get-policy*)
  - Bash(aws iam get-role-policy*)
  - Bash(aws iam list-attached-role-policies*)
  - Bash(aws ec2 describe-subnets*)
  - Bash(aws service-quotas list-service-quotas*)
  - Bash(agentcore status*)
---

# AgentCore Production-Readiness Review

Audit what actually exists — code, config, and deployed resources — against the checklist below. Produce a report, not vibes.

## Method

1. **Inventory reality first.** Read the project (`agentcore/agentcore.json`, agent code, IaC). Where the user permits, inspect deployed state with read-only AWS CLI calls (`aws bedrock-agentcore-control list/get-*`, IAM `get-role`/`get-policy`, `aws ec2 describe-subnets` for VPC checks). Never guess at a config you can read.
2. **Verify volatile criteria live.** Current security best practices, quotas, and supported features come from `search_agentcore_docs` (the `runtime-security-best-practices` and `harness-security` devguide pages are the anchors) — the checklist below is the stable skeleton, the docs are the current letter.
3. **Report format**: one line per check — ✅ pass / ❌ fail / ⚠️ can't verify (say what access you'd need) — grouped by section, ordered blockers-first, each ❌ with a concrete fix (command, policy JSON, or config diff). End with a verdict: **ship / ship-with-risks (list them) / do-not-ship (blockers)**.
4. Severity: **Blocker** (exploitable or data-loss), **High** (will page you), **Advisory**. PoCs being demoed ≠ production: if posture is still PoC, scope the review to what the promotion plan needs.

## Checklist

### Security — IAM (most common blockers)
- [ ] Execution role is **not** the CLI-generated dev policy; least-privilege, scoped to specific ARNs (no `"Resource": "*"`)
- [ ] Trust policy has confused-deputy conditions: `aws:SourceAccount` + `aws:SourceArn` (verify the currently documented condition shape live — over-strict `ArnEquals` patterns have caused false AccessDenied; `ArnLike` may be required)
- [ ] Privilege ceiling holds: execution role ≤ privileges of allowed invokers
- [ ] `bedrock-agentcore:InvokeAgentRuntimeCommand` / `InvokeAgentRuntimeCommandShell` **not granted** to principals who shouldn't get arbitrary shell in the microVM (tool allowlists are not a security boundary against these APIs)
- [ ] `InvokeAgentRuntimeForUser` explicitly denied where user-id delegation isn't used
- [ ] Cross-account: resource policies on both runtime **and** endpoint
- [ ] Policies validated with IAM Access Analyzer

### Security — identity & secrets
- [ ] Inbound auth matches the caller model (IAM for services, OAuth/JWT for end users); IdP config reviewed
- [ ] No secrets in env vars, code, or images — credential providers / token vault only
- [ ] 3LO vs 2LO correct: downstream systems see the *user's* identity where required
- [ ] Backend enforces user↔session mapping and per-user session caps (AgentCore does not)
- [ ] Tool-boundary guardrails are deterministic (Cedar policies / IAM), not prompt-text-only
- [ ] Model-generated code runs only in Code Interpreter

### Networking
- [ ] VPC decision is deliberate (private resources ⇒ VPC; otherwise default public is fine — reflexive VPC is a finding too)
- [ ] If VPC: ≥2 private subnets in **supported AZ IDs** (verify against live table); internet egress via NAT (not "public subnet"); VPC endpoints preferred for AWS services; Flow Logs enabled
- [ ] If no-public-internet requirement: PrivateLink endpoints for inbound API calls
- [ ] Org enforcement where mandated: `bedrock-agentcore:subnets`/`securityGroups` condition keys

### Reliability & operations
- [ ] Production clients invoke a **named endpoint pinned to a version** — never latest
- [ ] Execution limits set (`maxIterations`, `timeoutSeconds`, `maxTokens`, idle/lifetime)
- [ ] Resources owned by IaC in CI/CD, not CLI state; `--dry-run`/`cdk diff` gating in the pipeline
- [ ] Rollback plan: previous version retained + endpoint repoint procedure
- [ ] Quotas checked against expected load (live quotas page); increases filed
- [ ] Long-running work uses async patterns, not held sync connections

### Observability & quality
- [ ] Tracing/logs/metrics on in prod (and staging); traces confirmed flowing in CloudWatch
- [ ] Alarms: error rate, p95 latency, token consumption (cost-runaway detection)
- [ ] Evaluations wired and used as a release gate, not a dashboard
- [ ] Session/PII data handling reviewed (log redaction, retention, encryption at rest — check current encryption options live)

### Cost
- [ ] Cost model estimated from **live pricing** (FAQ source), formula shown, date-stamped
- [ ] Token/iteration limits function as the cost circuit-breaker; billing alarms set

## Handoffs

Fixes to code/config → `/aws-agentcore:build`. Redeploy and verification → `/aws-agentcore:deploy`. If findings reveal the architecture is wrong (e.g., auth mode is a one-way door that was missed) → `/aws-agentcore:architect`.
