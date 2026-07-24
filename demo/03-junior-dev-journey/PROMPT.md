# Demo: Junior Dev Journey

**Persona:** Junior developer, never built an AI agent before
**Story:** First agent → add memory → add tools → fix a deployment error (progressive learning)

---

## Prompt 1 — Where do I even start?

```
I'm a junior developer and my manager told me to build a chatbot that answers questions about our products. I know Python and I've deployed a Lambda function once, but I've never built an AI agent.

I don't know what framework to pick, what model to use, or how this works. Can you walk me through it step by step? Like really step by step — what to install, what to run, how to test it. Assume I know nothing about agents.
```

---

## Prompt 2 — Make it remember things

```
Cool, that worked! But right now every conversation starts fresh. My manager wants the agent to remember things about customers — like if someone said "my name is Sarah" last week, it should know that next time.

How does memory even work with AI? They don't have brains. And how do I add it to what I just built? Show me exactly what code changes.
```

---

## Prompt 3 — Give it superpowers

```
This is going great. But the agent just makes stuff up when it doesn't know an answer. I want it to be able to:
- Search the internet when it doesn't know something
- Actually visit a webpage and read it
- Run Python code when it needs to calculate things

Is this hard? My manager said it should be easy but I'm imagining building a web scraper and a code sandbox from scratch...
```

---

## Prompt 4 — Something broke

```
I ran `agentcore deploy` and it was working yesterday but now I'm getting this:

Error: CloudFormation stack update failed
  Resource: AgentRuntime
  Status: CREATE_FAILED
  Reason: User: arn:aws:iam::123456789012:user/junior-dev is not authorized to perform: bedrock-agentcore:CreateAgentRuntime

I didn't change anything! Why did it work before? What permissions do I need? My manager is on vacation and I don't know who to ask about IAM stuff.
```

---

## What it exercises
- Guided onboarding (Flow 1) — no jargon, step-by-step
- Memory explanation and integration (Flow for building)
- Tool addition (web search, browser, code interpreter)
- Troubleshooting (IAM error diagnosis + fix)
- Adapts language to junior developer level throughout
