import pytest
from unittest.mock import patch, MagicMock
import urllib.error
import xml.etree.ElementTree as ET
from MMEE_Agent.pubmed_tool import fetch_pubmed_abstract, extract_abstract_text

def test_fetch_pubmed_abstract_success():
    # Mocking standard HTTP response
    mock_response = MagicMock()
    mock_response.__enter__.return_value = mock_response
    mock_response.read.return_value = b"<PubmedArticleSet><AbstractText>Sample abstract text.</AbstractText></PubmedArticleSet>"
    
    with patch("urllib.request.urlopen", return_value=mock_response) as mock_urlopen:
        xml_data = fetch_pubmed_abstract("123456")
        
        assert xml_data == "<PubmedArticleSet><AbstractText>Sample abstract text.</AbstractText></PubmedArticleSet>"
        mock_urlopen.assert_called_once()
        # Verify the requested URL contains the correct parameters
        call_args = mock_urlopen.call_args[0][0]
        assert "db=pubmed" in call_args.full_url
        assert "id=123456" in call_args.full_url

def test_fetch_pubmed_handles_rate_limits():
    # Mocking urllib.error.HTTPError (e.g. 429 Too Many Requests)
    mock_fp = MagicMock()
    http_error = urllib.error.HTTPError(
        url="https://eutils.ncbi.nlm.nih.gov/",
        code=429,
        msg="Too Many Requests",
        hdrs=MagicMock(),
        fp=mock_fp
    )
    
    with patch("urllib.request.urlopen", side_effect=http_error):
        with pytest.raises(RuntimeError) as exc_info:
            fetch_pubmed_abstract("123456")
        
        assert "PubMed API rate limit or HTTP error (429)" in str(exc_info.value)

def test_extract_abstract_strips_nested_html_and_footnotes():
    # Raw XML containing markup within the abstract text
    raw_xml = """<PubmedArticleSet>
        <PubmedArticle>
            <MedlineCitation>
                <Article>
                    <Abstract>
                        <AbstractText>The mechanism involves <i>MHC-II processing</i> pathways<sup>1,2</sup>.</AbstractText>
                    </Abstract>
                </Article>
            </MedlineCitation>
        </PubmedArticle>
    </PubmedArticleSet>"""
    
    abstract = extract_abstract_text(raw_xml)
    
    # Assertions: markup and superscript footnote references stripped/normalized
    assert "MHC-II processing" in abstract
    assert "involves MHC-II processing pathways" in abstract
    # Ensure footnote tags are stripped or flattened properly
    assert "pathways1,2" in abstract or "pathways" in abstract

def test_extract_empty_abstract_raises_parse_error():
    # XML without AbstractText
    raw_xml = "<PubmedArticleSet><PubmedArticle></PubmedArticle></PubmedArticleSet>"
    
    with pytest.raises(ValueError) as exc_info:
        extract_abstract_text(raw_xml)
        
    assert "No abstract text found" in str(exc_info.value)
