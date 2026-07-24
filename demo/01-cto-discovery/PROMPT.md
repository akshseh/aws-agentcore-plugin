# Demo: CTO Discovery

**Persona:** CTO evaluating AgentCore for the first time
**Story:** Starts with "what is this?" → cost justification → comparison to current setup → decision

---

## Prompt 1 — What is this?

```
I keep hearing about AgentCore from our engineering team. I don't have time to read a hundred docs. In 2 minutes, tell me what it is, what problems it solves, and why I should care. We currently run AI agents on EKS and it's a headache.
```

---

## Prompt 2 — Cost justification

```
We run 3 m5.xlarge nodes 24/7 for our agent workload. That's $1,100/month just for compute. We handle 800 sessions/day, each lasting 4 minutes, but the agent is mostly idle waiting for model responses. What would this cost on AgentCore and how does the pricing model differ?
```

---

## Prompt 3 — Make the decision

```
My team proposed three options:
- A: Stay on EKS (what we have)
- B: Move to Lambda + Step Functions
- C: Use AgentCore

We need: session isolation, persistent memory, 5 API integrations with OAuth, auto-scaling from zero, full tracing, and we want to keep using LangGraph.

Give me a comparison table and your recommendation. Be direct — I have a meeting in 10 minutes.
```

---

## What it exercises
- Component discovery (list_agentcore_components)
- Cost estimation from FAQ source
- Compare mode (AgentCore vs EKS vs Lambda)
- Concise, CTO-appropriate communication
