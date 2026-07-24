# Demo: Tech Lead — Build and Ship

**Persona:** Tech lead taking a project from requirements to production
**Story:** Requirements → architecture → code → gateway + policies → CDK infrastructure → production hardening (one continuous flow)

---

## Prompt 1 — The requirements

```
I need to build a customer support agent. Here's what it needs:

1. Customers log in via Cognito. Agent should know who it's talking to.
2. Remembers previous conversations with each customer across sessions.
3. Looks up order status (Lambda: get_order_status, takes order_id)
4. Searches our FAQ knowledge base (Lambda: search_kb, takes query)
5. For refunds over $100, pauses and gets human approval before processing.
6. Full tracing of every decision the agent makes.

What's the architecture? Show me a diagram.
```

---

## Prompt 2 — Build the agent

```
Good architecture. Now give me the complete agent code in Python. Use whatever framework you recommend. I also need:
- The memory configuration (semantic + user preference strategies)
- The tool connectivity for those two Lambdas
- The inline function for human approval

Make it production-quality, not a toy example.
```

---

## Prompt 3 — Access control

```
Actually, I realized I need access control on those tools. The agent should only call get_order_status if the customer provides their order ID (not fish for random orders). And the escalate_to_human tool should only fire when the refund amount exceeds $100. Can you write policies for this?
```

---

## Prompt 4 — Infrastructure

```
Give me the full CDK TypeScript stack. Include: the runtime, memory store, gateway with both Lambda targets, the policies, inbound JWT auth via our Cognito pool, and observability. I want one deployable file. Assume VPC and Cognito already exist — I'll pass their IDs as CDK context.
```

---

## Prompt 5 — Ship it

```
Before I hand this to my team to deploy — what are we missing for production? Give me a prioritized checklist. Then give me the exact deploy commands, step by step, assuming a fresh AWS account with just the VPC and Cognito already set up.
```

---

## Supporting files

Provide these to Claude as context if needed:

- `tool_schemas.json` — tool definitions for the two Lambdas
- `cdk_context.json` — example CDK context parameters

---

## What it exercises
- Architecture with diagrams (Flow 4)
- Full implementation (Build flow)
- Policy authoring (Gateway + Cedar)
- CDK infrastructure generation
- Production checklist (Flow 5)
- Deployment guidance
