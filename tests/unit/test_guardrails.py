import pytest
from unittest.mock import MagicMock
from MMEE_Agent.agent import before_model_guardrail, before_tool_guardrail

def test_before_model_guardrail_blocks_offensive():
    mock_ctx = MagicMock()
    mock_req = MagicMock()
    # Mocking llm_request.contents. Let's assume it checks for blocked words or unsafe input.
    # But wait, we decided: "Use a lightweight classifier prompt for before_model_callback or classifier_agent to dynamically determine if the input is unsafe/off-topic."
    # Wait, if before_model_callback is just running a lightweight LLM check, let's see how it's implemented.
    # In before_model_callback, if we want to run a quick classification, we could also inspect if the user's prompt contains known bad words as a first layer,
    # or let the classifier_agent handle it.
    # Wait, the user answered: "Yes, add 'is_safe: bool' and 'safety_reason: str' to the QueryMetadata Pydantic schema and let the classifier_agent handle both safety and classification."
    # So the classifier_agent itself performs the safety classification!
    # Then what does before_model_callback do?
    # Ah! The before_model_callback can look at the session state. If classifier_agent ran and set is_safe = False, or if a query is flagged, we can prevent future LLM calls (e.g. to reviser or critic) by checking session state!
    # Yes! In before_model_callback, we check if ctx.session.state.get("query_metadata") exists and has is_safe == False, or if the input is already known to be blocked.
    # Let's verify this design!
    mock_ctx.session.state = {"query_metadata": {"is_safe": False, "safety_reason": "Unsafe topic"}}
    
    # When before_model_callback runs for subsequent steps, it should block.
    res = before_model_guardrail(mock_ctx, mock_req)
    assert res is not None
    res_text = res.content.parts[0].text.lower()
    assert "rejection" in res_text or "blocked" in res_text or "unsafe" in res_text

def test_before_tool_guardrail_blocks_invalid_path():
    mock_tool = MagicMock()
    mock_tool.name = "save_to_knowledge_base"
    mock_ctx = MagicMock()
    
    # Target file contains traversal attempt
    args = {
        "concept_id": "../malicious",
        "layer": 1,
        "dependencies": [],
        "content": "analog content"
    }
    
    res = before_tool_guardrail(mock_tool, args, mock_ctx)
    assert res is not None
    assert "error" in res or "Violation" in res.get("error", "")
