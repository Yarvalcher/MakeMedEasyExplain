import pytest
from MMEE_Agent.pubmed_tool import fetch_pubmed_abstract, extract_abstract_text

def test_live_pubmed_fetch_and_parse():
    # A known stable PubMed ID (PMID)
    pmid = "34351859"
    
    # 1. Fetch live XML from NCBI Entrez API
    try:
        raw_xml = fetch_pubmed_abstract(pmid)
    except Exception as e:
        pytest.fail(f"Live fetch failed. This could indicate rate-limiting, network issues, or API endpoint changes: {e}")
        
    assert "PubmedArticleSet" in raw_xml
    assert "<AbstractText>" in raw_xml
    
    # 2. Parse XML and extract abstract text
    abstract = extract_abstract_text(raw_xml)
    
    assert isinstance(abstract, str)
    assert len(abstract) > 100
    assert "visual acuity" in abstract.lower()
