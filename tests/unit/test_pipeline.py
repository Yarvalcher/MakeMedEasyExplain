import pytest
from unittest.mock import patch
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.events import Event
from google.genai import types

from MMEE_Agent.agent import root_agent

@pytest.mark.anyio
async def test_full_pipeline_success():
    async def mock_agent_run_async(self, ctx):
        if self.name == "classifier_agent":
            ctx.session.state["query_metadata"] = {
                "is_safe": True,
                "is_complex": True,
                "estimated_layer": 4,
                "core_concept": "t_cell"
            }
            ctx.session.events.append(
                Event(author="user", content=types.Content(role="user", parts=[types.Part.from_text(text="what is a t cell")]))
            )
            yield Event(author="classifier_agent", content=types.Content(parts=[types.Part.from_text(text="Classified complex")]))
        elif self.name == "critic_agent":
            yield Event(author="critic_agent", content=types.Content(parts=[types.Part.from_text(text="Facts PMID: 34351859")]))
        elif self.name == "reviser_agent":
            ctx.session.state["analogy"] = "A T-cell acts like a lock and key security guard."
            yield Event(author="reviser_agent", content=types.Content(parts=[types.Part.from_text(text="Analogy draft")]))
        else:
            yield Event(author=self.name, content=types.Content(parts=[types.Part.from_text(text="Mock event")]))

    # Patch at the LLM Agent class level and force local index to miss so critic runs
    with patch("google.adk.agents.llm_agent.Agent.run_async", new=mock_agent_run_async), \
         patch("MMEE_Agent.agent.search_local_biology_textbook", return_value="No results found"), \
         patch("MMEE_Agent.agent.save_to_knowledge_base") as mock_save:
         
        mock_save.return_value = "Saved successfully"
        
        session_service = InMemorySessionService()
        session_id = "test_sess_123"
        await session_service.create_session(app_name="MakeMedEasyExplain", user_id="user", session_id=session_id)
        
        runner = Runner(agent=root_agent, app_name="MakeMedEasyExplain", session_service=session_service)
        
        events = []
        async for event in runner.run_async(
            user_id="user",
            session_id=session_id,
            new_message=types.Content(role="user", parts=[types.Part.from_text(text="what is a t cell")])
        ):
            events.append(event)
            
        # Verify that save_to_knowledge_base was invoked with the approved analogy & PMID citation
        mock_save.assert_called_once()
        args, kwargs = mock_save.call_args
        assert args[0] == "t_cell"
        assert "34351859" in args[3]
        
        # Verify the saver yielded the output with success save message
        assert any("Saved successfully" in ev.content.parts[0].text for ev in events if ev.content and ev.content.parts)


@pytest.mark.anyio
async def test_full_pipeline_blocks_unapproved_analogy():
    async def mock_agent_run_async_fail(self, ctx):
        if self.name == "classifier_agent":
            ctx.session.state["query_metadata"] = {
                "is_safe": True,
                "is_complex": True,
                "estimated_layer": 4,
                "core_concept": "unapproved_concept"
            }
            ctx.session.events.append(
                Event(author="user", content=types.Content(role="user", parts=[types.Part.from_text(text="unapproved query")]))
            )
            yield Event(author="classifier_agent", content=types.Content(parts=[types.Part.from_text(text="Classified complex")]))
        elif self.name == "critic_agent":
            yield Event(author="critic_agent", content=types.Content(parts=[types.Part.from_text(text="Facts")]))
        elif self.name == "reviser_agent":
            # Returns a non-compliant analogy containing Layer 5 terms ("receptor", "ligand", "extracellular") without any metaphors
            ctx.session.state["analogy"] = "The receptor extracellular domain binds to the ligand."
            yield Event(author="reviser_agent", content=types.Content(parts=[types.Part.from_text(text="Analogy draft")]))
        else:
            yield Event(author=self.name, content=types.Content(parts=[types.Part.from_text(text="Mock event")]))

    with patch("google.adk.agents.llm_agent.Agent.run_async", new=mock_agent_run_async_fail), \
         patch("MMEE_Agent.agent.search_local_biology_textbook", return_value="No results found"), \
         patch("MMEE_Agent.agent.save_to_knowledge_base") as mock_save:
         
        session_service = InMemorySessionService()
        session_id = "test_sess_456"
        await session_service.create_session(app_name="MakeMedEasyExplain", user_id="user", session_id=session_id)
        
        runner = Runner(agent=root_agent, app_name="MakeMedEasyExplain", session_service=session_service)
        
        events = []
        async for event in runner.run_async(
            user_id="user",
            session_id=session_id,
            new_message=types.Content(role="user", parts=[types.Part.from_text(text="unapproved query")])
        ):
            events.append(event)
            
        # Verify SaveAgent did not commit the analogy and returned an error event
        mock_save.assert_not_called()
        error_events = [ev for ev in events if ev.content and ev.content.parts and "Error: Could not generate" in ev.content.parts[0].text]
        assert len(error_events) > 0
