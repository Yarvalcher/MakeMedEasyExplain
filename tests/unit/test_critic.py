import pytest
from unittest.mock import patch, MagicMock
from MMEE_Agent.sub_agents.critic.agent import (
    fetch_and_parse_pubmed_abstract,
    search_pubmed_with_fallback
)

@patch("MMEE_Agent.sub_agents.critic.agent.fetch_pubmed_abstract")
@patch("MMEE_Agent.sub_agents.critic.agent.extract_abstract_text")
def test_fetch_and_parse_pubmed_abstract_success(mock_extract, mock_fetch):
    mock_fetch.return_value = "<xml>abstract</xml>"
    mock_extract.return_value = "This is a clean abstract."
    
    res = fetch_and_parse_pubmed_abstract("12345")
    assert res == "This is a clean abstract."
    mock_fetch.assert_called_once_with("12345")
    mock_extract.assert_called_once_with("<xml>abstract</xml>")


@patch("MMEE_Agent.sub_agents.critic.agent.fetch_pubmed_abstract")
@patch("MMEE_Agent.sub_agents.critic.agent.web_search")
def test_fetch_and_parse_pubmed_abstract_failover(mock_web_search, mock_fetch):
    mock_fetch.side_effect = RuntimeError("Rate Limit")
    mock_web_search.return_value = "Web fallback results"
    
    res = fetch_and_parse_pubmed_abstract("12345")
    assert "PubMed fetch failed" in res
    assert "Web fallback results" in res
    mock_web_search.assert_called_once_with("PubMed PMID 12345 abstract")


@patch("MMEE_Agent.sub_agents.critic.agent.search_pubmed")
def test_search_pubmed_with_fallback_success(mock_search):
    mock_search.return_value = ["123", "456"]
    
    res = search_pubmed_with_fallback("Hepatitis")
    assert "Found PubMed articles with PMIDs: 123, 456" in res
    mock_search.assert_called_once_with("Hepatitis")


@patch("MMEE_Agent.sub_agents.critic.agent.search_pubmed")
@patch("MMEE_Agent.sub_agents.critic.agent.web_search")
def test_search_pubmed_with_fallback_no_results(mock_web_search, mock_search):
    mock_search.return_value = []
    mock_web_search.return_value = "Web results for Hepatitis"
    
    res = search_pubmed_with_fallback("Hepatitis")
    assert "No PMIDs found on PubMed" in res
    assert "Web results for Hepatitis" in res
    mock_web_search.assert_called_once_with("Hepatitis")


@patch("MMEE_Agent.sub_agents.critic.agent.search_pubmed")
@patch("MMEE_Agent.sub_agents.critic.agent.web_search")
def test_search_pubmed_with_fallback_api_error(mock_web_search, mock_search):
    mock_search.side_effect = RuntimeError("Service Unavailable")
    mock_web_search.return_value = "Web results for Hepatitis"
    
    res = search_pubmed_with_fallback("Hepatitis")
    assert "PubMed search failed" in res
    assert "Web results for Hepatitis" in res
    mock_web_search.assert_called_once_with("Hepatitis")
