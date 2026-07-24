# Demo: Migration Story

**Persona:** Engineering lead with existing agents on EKS, wants to migrate
**Story:** Show existing code → translate with minimal changes → add new capabilities that were too hard before → deploy

---

## Prompt 1 — We have three agents, different frameworks

```
We have three agents built by different teams, all running on EKS. I want them all on a managed platform by end of quarter. Here's what we have:

Agent 1 (platform team, Strands):
- Weather lookup agent
- File: agent_strands.py

Agent 2 (marketing team, CrewAI):
- Content research + writing pipeline
- File: agent_crewai.py

Agent 3 (legacy, bare Python):
- Direct Bedrock API calls, no framework
- File: agent_plain_python.py

Show me the minimal changes for each one. I want a side-by-side diff — what we have today vs what it looks like running on the managed platform.
```

---

## Prompt 2 — Now add what we couldn't do before

```
That was easy. Now here's why we're actually migrating — these are things we couldn't do on EKS without months of work:

1. Agent 1 should remember user preferences across sessions (we had to build our own Redis-based memory and it's buggy)
2. Agent 2 needs its researcher to browse actual web pages (we tried Puppeteer in a container and it was a nightmare)
3. Agent 3 needs proper OAuth so our mobile app users can call it directly (right now we have a hacky API Gateway + Lambda authorizer)

Show me how to add each capability. I want to see how little effort this takes compared to what we had to build ourselves.
```

---

## Prompt 3 — Observability and safe rollout

```
Last thing. On EKS we had no visibility into what the agents were actually doing — just CloudWatch logs we'd grep through when something broke. And deployments were terrifying because if we broke the prompt, we broke it for everyone.

Set up:
1. Full tracing so we can see every decision each agent makes
2. Quality monitoring — are the agents actually helpful?
3. A way to test prompt changes on 10% of traffic before rolling out

And give me the deployment workflow. How does the team ship changes safely going forward?
```

---

## Supporting files

```python
# agent_strands.py
from strands import Agent
from strands.models import BedrockModel
from strands.tools import tool

@tool
def get_weather(city: str) -> str:
    """Get current weather for a city."""
    return f"72°F in {city}"

agent = Agent(
    model=BedrockModel(model_id="anthropic.claude-sonnet-4-20250514"),
    tools=[get_weather],
    system_prompt="You are a helpful weather assistant.",
)
```

```python
# agent_crewai.py
from crewai import Agent, Task, Crew

researcher = Agent(role="Researcher", goal="Find market trends", backstory="Expert analyst")
writer = Agent(role="Writer", goal="Write blog posts", backstory="Content specialist")
task = Task(description="Research AI agent trends and write a blog post", agent=researcher)
crew = Crew(agents=[researcher, writer], tasks=[task])
```

```python
# agent_plain_python.py
import boto3

bedrock = boto3.client("bedrock-runtime")

def handle_request(user_message):
    response = bedrock.converse(
        modelId="anthropic.claude-sonnet-4-20250514",
        messages=[{"role": "user", "content": [{"text": user_message}]}],
    )
    return response["output"]["message"]["content"][0]["text"]
```

---

## What it exercises
- Framework translation (Flow 6) — 3 different frameworks
- Migration assistant (Flow 2) — minimal diffs
- Adding capabilities (memory, browser, auth)
- Observability and evaluations
- Safe deployment with versioning and A/B testing
