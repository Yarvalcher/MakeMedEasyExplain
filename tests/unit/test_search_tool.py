import pytest
from unittest.mock import patch, MagicMock
from MMEE_Agent.search_tool import web_search

def test_web_search_success():
    mock_response = MagicMock()
    mock_response.__enter__.return_value = mock_response
    mock_response.read.return_value = b"""
    <html>
        <table>
            <tr>
                <td class='result-snippet'>Hepatitis A is highly contagious.</td>
            </tr>
            <tr>
                <td class="result-snippet">Hepatitis B is spread through blood.</td>
            </tr>
        </table>
    </html>
    """
    
    with patch("urllib.request.urlopen", return_value=mock_response) as mock_urlopen:
        result = web_search("hepatitis differences")
        
        assert "Hepatitis A is highly contagious." in result
        assert "Hepatitis B is spread through blood." in result
        mock_urlopen.assert_called_once()
        
        # Verify post request parameters
        call_args = mock_urlopen.call_args[0][0]
        assert call_args.data == b"q=hepatitis+differences"
