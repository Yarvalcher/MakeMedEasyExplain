import pytest
import json
import urllib.error
from unittest.mock import patch, MagicMock
from MMEE_Agent.tools.github_tool import commit_to_github

@patch.dict("os.environ", {"GITHUB_PAT": "fake_token"})
def test_gitops_commit_blocks_outside_knowledge_base():
    # Blocks file path injection attempts or non-markdown extensions
    res1 = commit_to_github("test.py", "print('hello')")
    assert "Error: Security violation" in res1
    
    res2 = commit_to_github("../test.md", "some text")
    assert "Error: Security violation" in res2

@patch.dict("os.environ", {"GITHUB_PAT": "fake_token"})
@patch("urllib.request.urlopen")
def test_gitops_commit_success_new_file(mock_urlopen):
    # Mocking 404 (Not Found) for GET request (meaning new file)
    mock_get_error = urllib.error.HTTPError(
        url="https://api.github.com/repos/Yarvalcher/MakeMedEasyExplain/contents/knowledge_base/new_file.md",
        code=404,
        msg="Not Found",
        hdrs=MagicMock(),
        fp=MagicMock()
    )
    
    # Mocking 201 Created for PUT request
    mock_put_response = MagicMock()
    mock_put_response.__enter__.return_value = mock_put_response
    mock_put_response.read.return_value = b'{"content": {"name": "new_file.md"}}'
    
    # URLopen returns the error for GET, and response for PUT
    mock_urlopen.side_effect = [mock_get_error, mock_put_response]
    
    res = commit_to_github("new_file.md", "Analogy content")
    assert "Successfully committed new_file.md" in res
    assert mock_urlopen.call_count == 2

@patch.dict("os.environ", {"GITHUB_PAT": "fake_token"})
@patch("urllib.request.urlopen")
def test_gitops_commit_success_update(mock_urlopen):
    # Mocking 200 OK for GET request with existing file SHA
    mock_get_response = MagicMock()
    mock_get_response.__enter__.return_value = mock_get_response
    mock_get_response.read.return_value = b'{"sha": "existing_sha_12345"}'
    
    # Mocking 200 OK for PUT request
    mock_put_response = MagicMock()
    mock_put_response.__enter__.return_value = mock_put_response
    mock_put_response.read.return_value = b'{"content": {"name": "existing.md"}}'
    
    mock_urlopen.side_effect = [mock_get_response, mock_put_response]
    
    res = commit_to_github("existing.md", "Updated Analogy content")
    assert "Successfully committed existing.md" in res
    assert mock_urlopen.call_count == 2
    
    # Verify that the payload sent to PUT request contained the SHA
    put_call_data = json.loads(mock_urlopen.call_args_list[1][0][0].data.decode("utf-8"))
    assert put_call_data["sha"] == "existing_sha_12345"
