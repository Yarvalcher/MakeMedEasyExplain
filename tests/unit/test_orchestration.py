import pytest
from unittest.mock import MagicMock, patch
from MMEE_Agent.orchestrator import run_orchestration_loop

def test_supervisor_routes_to_educator_first():
    mock_educator = MagicMock(return_value="Safe analogy")
    # Validator returns APPROVED on first run
    mock_validator = MagicMock(return_value={
        "factual_drift_detected": False,
        "prescriptive_advice_detected": False,
        "reasoning": "Aligned",
        "status": "APPROVED"
    })
    
    with patch("MMEE_Agent.orchestrator.generate_analogy", mock_educator), \
         patch("MMEE_Agent.orchestrator.validate_analogy", mock_validator):
         
        result = run_orchestration_loop(abstract="Raw scientific abstract", max_retries=3)
        
        assert result["status"] == "APPROVED"
        assert result["analogy"] == "Safe analogy"
        mock_educator.assert_called_once_with("Raw scientific abstract", feedback="")
        mock_validator.assert_called_once_with("Safe analogy", "Raw scientific abstract")

def test_routing_loop_terminates_after_max_retries():
    # Educator is called multiple times due to failures
    mock_educator = MagicMock(side_effect=["Hallucination 1", "Hallucination 2", "Hallucination 3"])
    # Validator constantly returns REJECTED
    mock_validator = MagicMock(return_value={
        "factual_drift_detected": True,
        "prescriptive_advice_detected": False,
        "reasoning": "Factual drift found",
        "status": "REJECTED"
    })
    
    with patch("MMEE_Agent.orchestrator.generate_analogy", mock_educator), \
         patch("MMEE_Agent.orchestrator.validate_analogy", mock_validator):
         
        result = run_orchestration_loop(abstract="Raw scientific abstract", max_retries=2)
        
        # Should stop after max_retries (2 retries, meaning 3 attempts total)
        assert result["status"] == "REJECTED"
        assert mock_educator.call_count == 3
        assert mock_validator.call_count == 3
