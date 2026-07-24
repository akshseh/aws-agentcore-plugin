from crewai import Agent, Task, Crew

researcher = Agent(role="Researcher", goal="Find market trends", backstory="Expert analyst")
writer = Agent(role="Writer", goal="Write blog posts", backstory="Content specialist")
task = Task(description="Research AI agent trends and write a blog post", agent=researcher)
crew = Crew(agents=[researcher, writer], tasks=[task])
