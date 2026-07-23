# Amazon Bedrock AgentCore — Best Practices Guide

A comprehensive reference for building, deploying, and operating production-grade AI agents on AgentCore.

---

## Table of Contents

1. [Runtime](#1-runtime)
2. [Memory](#2-memory)
3. [Gateway](#3-gateway)
4. [Identity](#4-identity)
5. [Policy](#5-policy)
6. [Observability](#6-observability)
7. [Evaluations](#7-evaluations)
8. [Optimization](#8-optimization)
9. [Code Interpreter](#9-code-interpreter)
10. [Browser](#10-browser)
11. [Multi-Agent Architecture (A2A)](#11-multi-agent-architecture-a2a)
12. [Security (Cross-Cutting)](#12-security-cross-cutting)
13. [Cost Optimization](#13-cost-optimization)

---

## 1. Runtime

AgentCore Runtime is the serverless compute layer for deploying and scaling agents. It provides microVM-based session isolation, automatic scaling, and consumption-based billing.

### Deployment Strategy

- **Start with direct code-zip deployment** for rapid iteration during development. Move to container-based deployment only when you need custom system dependencies or advanced configurations.
- **Use the AgentCore CLI** (`agentcore create`, `agentcore deploy`, `agentcore invoke`) to scaffold, deploy, and test agents quickly.
- **Test locally first** before deploying. The CLI supports local testing with `agentcore test` to validate agent behavior without incurring cloud costs.

### Versioning and Endpoints

- **Use endpoint-based routing** to manage multiple environments. Create separate endpoints for dev, staging, and production that point to specific versions.
- **Never update the DEFAULT endpoint for production traffic.** Create a named production endpoint and explicitly promote versions to it after testing.
- **Versions are immutable once created.** Treat each version as a release artifact — if something breaks, point your endpoint back to a known-good version.

### Scaling and Performance

- **Don't over-provision.** AgentCore Runtime scales from zero to thousands of concurrent sessions automatically. There's no need for capacity planning.
- **Understand consumption-based billing.** You pay only for active CPU (per-second) and memory (peak per session). I/O wait time (waiting for LLM responses, tool calls, database queries) is free.
- **Keep agent startup lightweight.** Cold start time affects the first user in a session. Minimize heavy imports and initialization logic.
- **Use streaming responses** for better user experience. AgentCore supports bi-directional streaming via WebSocket for real-time conversational agents.

### Protocol Selection

- **HTTP** — Best for traditional request/response patterns with simple agents.
- **MCP** — Use when deploying tool servers that other agents consume.
- **A2A** — Use for multi-agent architectures where agents need to discover and communicate with each other.
- **AG-UI** — Use for agents that need to stream structured UI updates to frontend applications.

Choose the protocol based on your consumption pattern, not complexity. You can always change protocol later with a new version.

### Session Management

- Each session gets a **dedicated microVM** with isolated CPU, memory, and filesystem.
- **Design agents to be stateless across sessions.** Use AgentCore Memory for persistence, not in-memory state.
- **Set appropriate session timeouts.** Long-running async workloads can run up to 8 hours.

---

## 2. Memory

AgentCore Memory provides managed short-term (within session) and long-term (across sessions) memory for agents.

### Short-Term Memory

- **Write events as they happen.** Send conversation turns to memory immediately via `CreateEvent`, not in batches at the end.
- **Use structured message roles** (`USER`, `ASSISTANT`, `TOOL`) to help extraction strategies understand conversation flow.
- **Set appropriate event retention periods** (up to 365 days). Choose based on compliance requirements and your use case — you don't need to keep everything.

### Long-Term Memory

- **Start with built-in strategies** (`USER_PREFERENCE`, `SEMANTIC`, etc.) before building custom ones. They cover the majority of use cases with minimal configuration.
- **Use custom extraction strategies** only when built-in strategies don't capture what matters for your domain. You can provide your own model and prompt to extract exactly what you need.
- **Don't over-extract.** More memories isn't better — it adds noise to retrieval. Focus on extracting actionable information the agent will actually use.

### Memory Architecture

- **Use namespaces to segment memory** by user, project, or business unit. This keeps data isolated and retrieval fast.
- **Share long-term memory across agents** when multiple agents need the same context (e.g., user preferences). Use separate memory stores for agent-specific knowledge.
- **Design for memory poisoning prevention.** Validate and sanitize user input before writing to memory. Treat memory content as potentially adversarial when reading it back.

### Encryption and Security

- **Use a customer-managed KMS key (CMK)** for encryption when handling sensitive data. The service encrypts with a service-managed key by default, but CMK gives you control over key rotation and access policies.
- **Apply least-privilege access** to memory resources. Not every agent or service needs read/write access to all memory stores.

### Performance

- **Wait for memory to become ACTIVE** after creation before writing events. Poll the status or use a waiter.
- **Use semantic search** for long-term memory retrieval rather than loading all memories. Provide context about the current task for better retrieval relevance.
- **Set TTLs on memories** that have a natural expiration (e.g., temporary preferences, time-bound facts).

---

## 3. Gateway

AgentCore Gateway provides a unified MCP endpoint for agents to discover and invoke tools.

### Tool Organization

- **Group related tools into logical targets** (e.g., a "CRM" target for Salesforce tools, a "DevOps" target for GitHub/Jira tools). This improves discoverability and simplifies access control.
- **Write clear, descriptive tool names and descriptions.** Agents use these to decide which tool to invoke. Poor descriptions lead to poor tool selection.
- **Understand tool naming conventions.** Gateway names tools as `{TargetName}___{ToolName}`. Keep target names concise to avoid overly long tool identifiers.

### Semantic Search

- **Enable semantic search** when you have more than 10-15 tools in a gateway. It helps agents find the right tool without being overwhelmed by a full tool list.
- **Use metadata-based filtering** to control which tools agents can discover based on risk levels, categories, or permissions.

### Security

- **Configure inbound authorization** (IAM or OAuth) for every gateway. Never expose a gateway without authentication.
- **Use OAuth 2.1** when end-users need scoped, delegated access through the gateway.
- **Enable WAF (Web ACL)** to filter malicious requests before they reach your tools.
- **Apply Policy (Cedar)** for fine-grained, real-time authorization on every tool call (see [Policy section](#5-policy)).

### Integration Patterns

- **Use pre-built connectors** for popular services (Salesforce, Slack, Jira, Zendesk) instead of building custom integrations.
- **Prefer Lambda-based targets** for lightweight tools that don't need persistent compute.
- **Use AgentCore Runtime targets** when your tool is itself an agent or needs session-level state.
- **Connect to existing MCP servers** directly — no need to rewrite them as Lambda functions.

### Reliability

- **Implement idempotent tools.** Agents may retry tool calls due to timeouts or errors. Your tools should handle duplicate invocations gracefully.
- **Set appropriate timeouts** on targets. A tool that takes 30 seconds should not have a 5-second timeout.
- **Return structured error messages** that help the agent understand what went wrong and whether to retry.

---

## 4. Identity

AgentCore Identity manages OAuth flows, token vaulting, and credential delegation for agents.

### Authentication Architecture

- **Use your existing identity provider** (Cognito, Entra ID, Okta) rather than creating a new one. AgentCore Identity integrates natively with them.
- **Configure the AgentCore Identity authorizer** on your Runtime to enforce who can invoke your agent.
- **Separate user identity from agent identity.** The agent should have its own IAM role and credentials, distinct from the end-user's tokens.

### OAuth and Token Management

- **Use 3LO (authorization code grant)** when agents act on behalf of users — this gives users explicit control over what the agent can do.
- **Use 2LO (client credentials grant)** for machine-to-machine scenarios where the agent acts as itself.
- **Let AgentCore handle token refresh.** The token vault automatically refreshes expired tokens using stored refresh tokens, reducing consent fatigue for end-users.
- **Scope tokens narrowly.** Request only the OAuth scopes the agent actually needs for its current task.

### Credential Security

- **Never store credentials in agent code or environment variables.** Use the AgentCore Identity token vault for all OAuth tokens and API keys.
- **Enable session binding** for OAuth authorization URLs to prevent CSRF attacks.
- **Rotate client secrets** on a regular schedule and update them in AgentCore Identity.

### Multi-Tenant Patterns

- **Use custom claims** to implement tenant-level access control in multi-tenant environments.
- **Namespace token storage by user ID** so one user's tokens can never be accessed by another user's agent session.

---

## 5. Policy

AgentCore Policy enforces real-time authorization on agent actions using Cedar policies integrated with Gateway.

### Policy Design

- **Start with a default-deny posture.** Only permit actions that are explicitly allowed.
- **Keep policies simple and composable.** Many focused policies are easier to audit than one monolithic policy.
- **Use natural language policy authoring** to generate initial Cedar policies, then validate and refine them.
- **Test policies before deploying.** Use automated reasoning to identify policies that are overly permissive, overly restrictive, or contain unsatisfiable conditions.

### Common Patterns

- **Emergency shutdown** — A single `forbid(principal, action, resource)` policy disables all tool calls instantly during incidents.
- **Role-based access** — Use principal attributes (OAuth claims, IAM tags) to scope permissions by role.
- **Rate limiting by action** — Restrict how many times specific high-risk tools (e.g., refund processing) can be called per session.
- **Time-based restrictions** — Permit certain actions only during business hours or specific maintenance windows.
- **Data classification** — Block agents from accessing tools that expose PII unless the user has appropriate clearance.

### Operational Best Practices

- **Separate policy management from agent development.** Security teams should own policies; agent developers should not need to embed authorization logic in prompts.
- **Version your policies alongside your agent code.** Policy changes should go through the same review and approval process.
- **Use forbid-wins semantics intentionally.** A `forbid` policy always overrides a `permit`. Use this for hard guardrails that should never be bypassed.
- **Integrate Bedrock Guardrails with Policy** to detect prompt injection and sensitive data exposure at the Gateway layer.

### Monitoring

- **Monitor policy evaluation metrics** (invocations, denials, latency) in CloudWatch.
- **Alert on unexpected denial spikes** — they may indicate a misconfigured policy or a misbehaving agent.
- **Audit policy changes** through CloudTrail for compliance.

---

## 6. Observability

AgentCore Observability provides tracing, metrics, and monitoring across all AgentCore services.

### Setup

- **Enable observability from day one.** Don't wait until you have a production issue to add tracing. It's far easier to instrument early.
- **Enable CloudWatch Transaction Search** (one-time setup) to view AgentCore spans in the generative AI observability dashboard.
- **For Runtime-hosted agents**, observability is configured at the Runtime level. For non-hosted agents, use the SDK's OpenTelemetry integration.

### Tracing Best Practices

- **Add custom attributes to traces** — include business-relevant metadata (user ID, tenant, workflow name) that helps you filter and correlate issues.
- **Use span-level detail** to understand individual steps: which tool was called, what the LLM decided, how long each step took.
- **Correlate traces across sub-agents.** When using A2A, ensure trace context propagates between orchestrator and sub-agents.

### Metrics and Dashboards

- **Monitor key metrics**: session count, latency (p50/p95/p99), duration, token usage, and error rates.
- **Set up CloudWatch alarms** for error rate spikes, latency degradation, and token usage anomalies.
- **Use cross-account monitoring** for multi-account architectures to get a single pane of glass.

### Integration with Third-Party Tools

- **Export telemetry via OpenTelemetry** to your existing monitoring stack (Datadog, Dynatrace, Arize Phoenix, Langfuse, LangSmith, etc.).
- **Don't duplicate instrumentation.** Use AgentCore's service-vended spans as the source of truth and export them to your platform of choice.

### What to Watch For

- **Silent failures** — Agents that return a response but didn't actually complete the task. Track goal success rate, not just error rates.
- **Token bloat** — Increasing token usage over time may indicate memory issues or prompt drift.
- **Tool selection patterns** — If an agent consistently calls the wrong tool first, your tool descriptions need improvement.
- **Latency outliers** — p99 latency spikes often indicate a specific tool or model call that's failing and retrying.

---

## 7. Evaluations

AgentCore Evaluations provides continuous, real-time quality scoring for agent interactions.

### Setting Up Evaluations

- **Start with built-in evaluators** for common dimensions: Correctness, Helpfulness, Faithfulness, Response Relevance, Tool Selection Accuracy, and Goal Success Rate.
- **Sample strategically.** You don't need to evaluate 100% of interactions — configure a sampling rate that gives statistical confidence without excessive cost.
- **Add custom evaluators** for business-specific quality criteria that built-in evaluators don't cover.

### Evaluator Selection by Use Case

| Use Case | Key Evaluators |
|----------|---------------|
| Customer support | Helpfulness, Goal Success Rate, Harmfulness |
| Research/RAG | Correctness, Faithfulness, Response Relevance |
| Code generation | Correctness, Instruction Following |
| Multi-step workflows | Tool Selection Accuracy, Tool Parameter Accuracy, Goal Success Rate |
| Safety-critical | Harmfulness, Stereotyping, Refusal |

### Operational Best Practices

- **Run evaluations on both online (live) and on-demand (batch) modes.** Online catches production regressions; on-demand validates changes before deployment.
- **Set quality baselines** early. Know what "good" looks like for your use case before you start optimizing.
- **Track evaluator scores over time** to detect gradual degradation that wouldn't trigger immediate alerts.
- **Use evaluation results to inform Optimization** — connect quality scores to specific agent behaviors.

### Custom Evaluators

- **Use code-based evaluators** for deterministic checks (regex matching, format validation, structured output verification).
- **Use LLM-based custom evaluators** for nuanced quality assessment that requires judgment.
- **Version your custom evaluator prompts** and track how prompt changes affect scoring consistency.

---

## 8. Optimization

AgentCore Optimization turns production traces into continuous improvement through failure analysis, recommendations, and A/B testing.

### Insights

- **Enable failure insights** to surface recurring silent failures — agent behaviors that look fine on dashboards but don't actually help users.
- **Use intent insights** to understand what users are actually trying to do. This often reveals gaps between your designed workflows and real usage patterns.
- **Use trajectory insights** to identify common execution paths vs. outliers. Outliers often indicate bugs or unhandled edge cases.

### Recommendations

- **Ground all changes in data.** Don't guess at prompt improvements — let Optimization analyze traces and evaluation outputs to suggest specific changes.
- **Validate recommendations with batch evaluation** before deploying. Run the suggested changes against a test dataset and compare aggregate scores.
- **Focus on system prompts and tool descriptions** first — these have the highest leverage on agent behavior.

### A/B Testing

- **Use A/B testing for any significant change** — model swaps, prompt rewrites, tool configuration changes.
- **Split live production traffic** to compare variants under real conditions, not just synthetic benchmarks.
- **Define success metrics before starting the test.** Decide what "better" means (latency? accuracy? cost?) and for how long you'll run the experiment.

### Continuous Improvement Loop

1. **Observe** — Collect traces and evaluation scores from production
2. **Analyze** — Run insights to surface problems and patterns
3. **Hypothesize** — Generate data-grounded recommendations
4. **Validate** — Test recommendations with batch evaluation
5. **Deploy** — Roll out via A/B test with live traffic
6. **Confirm** — Verify improvement holds at scale, then promote

---

## 9. Code Interpreter

AgentCore Code Interpreter provides sandboxed code execution for agents.

### When to Use

- **Data analysis and visualization** — Let agents write Python to analyze datasets and generate charts.
- **Mathematical computation** — When you need precise calculations, not LLM approximations.
- **Answer validation** — Have the agent verify its own answers by writing and executing test code.
- **File processing** — Parse, transform, and generate files programmatically.

### Best Practices

- **Use pre-built runtimes** (Python, JavaScript, TypeScript) with common libraries pre-installed. Only configure custom environments when you need specific packages.
- **Reference large files via S3** rather than passing them through the API. Code Interpreter supports direct S3 access for gigabyte-scale data.
- **Set session-level isolation** for sensitive workloads. Each code execution session is sandboxed, but configure VPC connectivity if the code needs access to internal resources.
- **Handle execution failures gracefully.** Code generated by LLMs often fails on the first attempt. Design your agent to retry with error context.
- **Set execution timeouts** appropriate for your workload. A data analysis task might need minutes; a simple calculation should timeout in seconds.

### Security

- **Never allow code execution with credentials embedded in the code.** Pass secrets via environment variables or secure parameter injection.
- **Use VPC configuration** when code needs to access internal APIs or databases.
- **Monitor code execution** through observability — watch for unusual patterns like network calls to unexpected endpoints.

---

## 10. Browser

AgentCore Browser provides cloud-based browser automation for agents to interact with websites.

### When to Use

- **Web scraping and data extraction** from sites without APIs.
- **Form filling and workflow automation** on behalf of users.
- **Testing and verification** of web-based outputs.
- **Multi-step web workflows** that require navigation, login, and interaction.

### Best Practices

- **Use federated identity integration** when the agent needs to log into sites as the user. Don't hardcode credentials.
- **Enable session replay** for debugging — it records all browser interactions for later inspection.
- **Use live viewing** during development to watch the agent interact with websites in real time.
- **Design for CAPTCHA handling.** AgentCore Browser reduces CAPTCHA interruptions, but plan for cases where manual intervention is needed.

### Security and Compliance

- **Enable VM-level isolation** for sensitive browsing sessions.
- **Configure VPC connectivity** if the browser needs to access internal web applications.
- **Use CloudTrail logging** for audit trails of all browser interactions.
- **Set session-level boundaries** — don't let one agent session's browser context leak into another.

### Performance

- **Keep browser sessions short-lived.** Close sessions when the task is complete to free resources.
- **Avoid overly broad scraping patterns.** Targeted interactions are faster and more reliable than full-page parsing.
- **Use structured selectors** (IDs, data attributes) over fragile CSS selectors when possible.

---

## 11. Multi-Agent Architecture (A2A)

AgentCore supports multi-agent systems through the Agent-to-Agent (A2A) protocol.

### Architecture Patterns

**Orchestrator + Specialists**
```
Orchestrator Agent (planning, routing)
  ├── Research Agent (web search, document retrieval)
  ├── Action Agent (API calls, data mutations)
  └── Review Agent (validation, quality checks)
```

**Peer-to-Peer**
```
Agent A ←→ Agent B ←→ Agent C
(Each agent discovers and calls others as needed)
```

**Hierarchical**
```
Supervisor Agent
  ├── Team Lead A
  │     ├── Worker A1
  │     └── Worker A2
  └── Team Lead B
        ├── Worker B1
        └── Worker B2
```

### Design Principles

- **Start monolithic, split later.** Build a single agent first, observe behavior in production, then decompose based on data (see [Optimization section](#8-optimization)).
- **Each sub-agent should be independently deployable and testable.** Don't create tight coupling between agents.
- **Define clear responsibilities.** If you can't describe what a sub-agent does in one sentence, it's doing too much.
- **Use Agent Cards for discovery.** Each A2A agent publishes a `/.well-known/agent-card.json` describing its capabilities.

### Communication Best Practices

- **Keep messages between agents structured.** Use clear schemas for requests and responses rather than free-form text.
- **Propagate context (trace IDs, user IDs, session IDs)** across agent boundaries for observability.
- **Handle partial failures.** If one sub-agent fails, the orchestrator should be able to continue or gracefully degrade.
- **Set timeouts on inter-agent calls.** A sub-agent that hangs shouldn't block the entire workflow.

### Scaling Considerations

- **Each sub-agent scales independently** on its own AgentCore Runtime. A burst in research requests doesn't affect the action agent.
- **Use different models for different agents.** A routing agent can use a cheaper/faster model; a complex reasoning agent needs a stronger model.
- **Don't over-decompose.** Each additional agent adds latency and complexity. Decompose only when it improves quality, cost, or maintainability.

---

## 12. Security (Cross-Cutting)

Security practices that apply across all AgentCore components.

### IAM and Access Control

- **Use least-privilege execution roles.** Don't use `BedrockAgentCoreFullAccess` in production — create custom policies scoped to your specific resources.
- **Use resource-based policies** for cross-account access rather than sharing credentials.
- **Prevent confused deputy attacks** by using `aws:SourceArn` and `aws:SourceAccount` conditions in trust policies.
- **Rotate credentials regularly** and use IAM roles over long-lived access keys.

### Network Security

- **Configure VPC connectivity** for agents that access internal resources. Don't expose internal services to the public internet just for agent access.
- **Use PrivateLink** for communication between AgentCore services and your VPC resources.
- **Restrict outbound network access** from agent sessions. Only allow connections to known, required endpoints.

### Data Protection

- **Encrypt at rest** using customer-managed KMS keys for sensitive workloads.
- **Encrypt in transit** — all AgentCore APIs use TLS by default.
- **Classify data flowing through your agents** and apply appropriate controls based on sensitivity.
- **Implement input validation** at every boundary — between users and agents, between agents and tools, between agents and memory.

### Prompt Injection Defense

- **Validate and sanitize user input** before it reaches the agent.
- **Use Policy to enforce guardrails** at the Gateway layer, outside the agent's control.
- **Integrate Bedrock Guardrails** for detecting prompt injection attempts.
- **Don't trust memory content blindly.** Memory could be poisoned by prior malicious input — validate retrieved memories before acting on them.

### Audit and Compliance

- **Enable CloudTrail** for all AgentCore API calls.
- **Use observability traces** as an audit trail of agent decisions and actions.
- **Retain logs** according to your compliance requirements.
- **Document your agent's capabilities and limitations** for security review.

---

## 13. Cost Optimization

### Runtime Costs

- **Leverage free I/O wait.** AgentCore Runtime doesn't charge for time spent waiting on LLM responses or tool calls — this alone can reduce costs 30-70% vs. container-based hosting.
- **Right-size your compute.** Monitor actual CPU and memory usage through observability and adjust configurations.
- **Scale to zero.** If your agent has low traffic periods, you pay nothing during idle time.

### Model Costs

- **Use different models for different tasks.** Route simple classification to a cheaper model; reserve expensive models for complex reasoning.
- **Cache common responses.** If your agent frequently answers the same questions, use memory to avoid redundant LLM calls.
- **Minimize token usage** — keep system prompts concise, use structured formats, and avoid stuffing unnecessary context.

### Memory Costs

- **Set appropriate retention periods.** Don't store events longer than needed.
- **Be selective with extraction strategies.** Every extraction call uses a model — don't extract from conversations that won't yield useful long-term memories.
- **Archive or delete memories** that are no longer relevant.

### Gateway Costs

- **Batch operations where possible.** A single well-designed tool call is cheaper than multiple small calls.
- **Cache tool responses** for read-heavy, slowly-changing data.
- **Use semantic search** to reduce the number of tools loaded into agent context, which reduces token costs downstream.

### Evaluation Costs

- **Sample judiciously.** Evaluate a representative subset rather than every interaction.
- **Use code-based evaluators** for checks that don't need LLM judgment — they're cheaper and faster.
- **Run on-demand evaluations** against curated test sets rather than evaluating all production traffic for pre-deployment validation.

---

## Quick Reference: Phased Adoption

| Phase | Components | Goal |
|-------|-----------|------|
| **POC** | Runtime + Gateway + 1 model | Prove the agent can solve your problem |
| **V1 Production** | + Memory + Identity + Observability + Policy | Ship a secure, monitored, context-aware agent |
| **V2 Scale** | + Evaluations + Optimization + A2A decomposition | Continuous improvement and multi-agent architecture |
| **Enterprise** | + Registry + Payments + Cross-account monitoring | Organization-wide governance and discovery |

---

## Further Reading

- [AgentCore Developer Guide](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/)
- [AgentCore CLI (GitHub)](https://github.com/aws/agentcore-cli)
- [AgentCore Python SDK (GitHub)](https://github.com/aws/bedrock-agentcore-sdk-python)
- [AgentCore Samples (GitHub)](https://github.com/awslabs/amazon-bedrock-agentcore-samples)
- [AgentCore FAQs](https://aws.amazon.com/bedrock/agentcore/faqs/)
- [AgentCore Pricing](https://aws.amazon.com/bedrock/agentcore/pricing/)
