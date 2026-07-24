# Demo: Platform at Scale

**Persona:** Tech lead designing an agent platform for multiple teams
**Story:** Multi-team architecture → shared gateway with policies → multi-agent collaboration → security review for launch

---

## Prompt 1 — Platform design

```
I'm the tech lead and I need to design our agent platform. We have 4 teams that will each build their own agents:

- Team Alpha: customer support agent (memory, tools, human escalation)
- Team Beta: data analyst agent (needs VPC access to our databases, runs code)
- Team Gamma: sales assistant (CRM integration, sends emails via OAuth)
- Team Delta: devops agent (calls AWS APIs, reads CloudWatch, creates tickets)

My requirements:
1. Each team deploys independently — different release cycles
2. Shared tool gateway — teams register tools, other agents can discover them
3. One auth system — Cognito user pool, agents scoped to user identity
4. All traces in one place — filterable by team and agent
5. Each team can't break others — guardrails and isolation

How should I structure this? Show me the platform architecture with clear ownership boundaries.
```

---

## Prompt 2 — Shared gateway with access control

```
Good. Now zoom into the shared gateway. I need strict access control:

- Only Team Alpha's agent can access customer PII
- Team Delta's devops agent can call AWS APIs but only read operations (no deletes)
- Team Gamma's sales agent gets Salesforce OAuth but only for the deals they own
- Any agent can create Jira tickets and search the knowledge base
- All tool calls must be auditable for compliance

Show me the gateway setup, the policies, and how new teams onboard their tools without needing a platform engineer to do it.
```

---

## Prompt 3 — Multi-agent collaboration

```
Here's the next challenge. Our teams want their agents to collaborate:

- Team Alpha's support agent should be able to ask Team Beta's data agent to pull order analytics
- Team Gamma's sales agent should trigger Team Delta's devops agent to provision a demo environment
- All cross-agent calls should be logged and governed by the same policies

How do agents talk to each other? What's the architecture for this? And how do we prevent agent A from calling agent B in an infinite loop?
```

---

## Prompt 4 — Security review before launch

```
Our security team needs to sign off before we go live. They'll ask:

1. How are agent sessions isolated from each other?
2. Where are third-party credentials stored?
3. What's the blast radius if an agent is compromised via prompt injection?
4. Can one team's agent access another team's data?
5. Full audit trail of every action?
6. Credential rotation — what happens when OAuth tokens expire?

Give me the answers with references. I need to walk into that meeting prepared.
```

---

## What it exercises
- Architecture with diagrams (multi-team platform design)
- Gateway + Cedar policies (fine-grained, multi-team)
- Multi-agent communication (A2A protocol)
- Security review preparation (Flow 5 adapted for security)
- Scales from single agent to full organizational platform
