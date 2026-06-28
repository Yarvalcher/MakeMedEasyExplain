from google.adk.agents.llm_agent import Agent

root_agent = Agent(
    model='gemini-2.5-flash',
    name='MMEE_Agent',
    description='MakeMedEasyExplain Supervisor Agent - democratizes medical literature.',
    instruction='Coordinate user sessions, route to simplification, and ensure safe visual analogies.',
)
