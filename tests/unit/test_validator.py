import pytest
from MMEE_Agent.tools.validator import validate_analogy

def test_validator_rejects_hallucinations():
    abstract = "Clinical trials show that Drug X reduces blood pressure by 10%."
    # The educator hallucinated a 90% reduction instead of 10%
    hallucinated_analogy = "Drug X is like a shield that blocks pressure, reducing it by 90%."
    
    result = validate_analogy(hallucinated_analogy, abstract)
    
    assert result["factual_drift_detected"] is True
    assert result["status"] == "REJECTED"
    assert "90%" in result["reasoning"] or "reduction" in result["reasoning"].lower()

def test_validator_rejects_medical_advice():
    abstract = "Drug X reduces blood pressure in patients with hypertension."
    # The educator injected clinical advice ("You should take this drug daily")
    advice_analogy = "Drug X acts like a gatekeeper. You should take this drug daily to treat your high blood pressure."
    
    result = validate_analogy(advice_analogy, abstract)
    
    assert result["prescriptive_advice_detected"] is True
    assert result["status"] == "REJECTED"
    assert "take this drug" in result["reasoning"].lower() or "should" in result["reasoning"].lower()

def test_validator_approves_safe_analogy():
    abstract = "Clinical trials show that Drug X reduces blood pressure by 10%."
    safe_analogy = "Drug X acts like a relief valve on a pipe, letting out a small portion (10%) of the high pressure."
    
    result = validate_analogy(safe_analogy, abstract)
    
    assert result["factual_drift_detected"] is False
    assert result["prescriptive_advice_detected"] is False
    assert result["status"] == "APPROVED"

@pytest.mark.anyio
async def test_validator_agent_bypasses_simple_concepts():
    from unittest.mock import MagicMock
    from MMEE_Agent.agent import ValidatorAgent
    from google.adk.events import EventActions

    # Create ValidatorAgent instance
    agent = ValidatorAgent(name="test_validator")
    
    # Mock context
    mock_ctx = MagicMock()
    mock_ctx.session.state = {
        "query_metadata": {"is_complex": False},
        "analogy": "Friendly description of teeth",
        "raw_facts": "Teeth are used to chew food."
    }
    
    # Run the agent async generator implementation
    events = []
    async for event in agent._run_async_impl(mock_ctx):
        events.append(event)
        
    assert len(events) == 2
    assert "APPROVED" in events[0].content.parts[0].text
    assert events[1].actions is not None
    assert events[1].actions.escalate is True

