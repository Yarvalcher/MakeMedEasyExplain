import urllib.request
import urllib.error
import urllib.parse
import json
import xml.etree.ElementTree as ET
from typing import List

def search_pubmed(query: str, max_results: int = 3) -> List[str]:
    """Searches PubMed for articles matching the query term and returns a list of PMIDs.
    
    Args:
        query: The search term or keywords (e.g. 'Hepatitis A').
        max_results: Max number of PMIDs to return.
        
    Returns:
        A list of PubMed ID strings (PMIDs).
    """
    cleaned_query = urllib.parse.quote_plus(query.strip())
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={cleaned_query}&retmode=json&retmax={max_results}"
    
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "MakeMedEasyExplain/1.0 (https://github.com/Yarvalcher/MakeMedEasyExplain)"}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            return res_data.get("esearchresult", {}).get("idlist", [])
    except Exception as e:
        raise RuntimeError(f"Failed to search PubMed: {e}")


def fetch_pubmed_abstract(pmid: str) -> str:
    """Queries the NCBI E-utilities API to retrieve the XML abstract for a given PMID.
    
    Args:
        pmid: PubMed ID string.
        
    Returns:
        The raw XML response string.
        
    Raises:
        RuntimeError: If the HTTP request fails or rate limits are hit.
    """
    # Clean the input PMID
    cleaned_pmid = str(pmid).strip()
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={cleaned_pmid}&retmode=xml"
    
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "MakeMedEasyExplain/1.0 (https://github.com/Yarvalcher/MakeMedEasyExplain)"}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = response.read()
            return data.decode("utf-8")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"PubMed API rate limit or HTTP error ({e.code}): {e.reason}")
    except Exception as e:
        raise RuntimeError(f"Failed to query PubMed API: {e}")

def extract_abstract_text(raw_xml: str) -> str:
    """Parses raw PubMed XML, isolates <AbstractText> nodes, and flattens/strips nested tags.
    
    Args:
        raw_xml: Raw XML string returned by NCBI E-utilities.
        
    Returns:
        The flattened, plain-text abstract.
        
    Raises:
        ValueError: If the XML is invalid or does not contain any AbstractText nodes.
    """
    try:
        root = ET.fromstring(raw_xml)
    except ET.ParseError as e:
        raise ValueError(f"Invalid XML payload: {e}")
        
    abstract_nodes = root.findall(".//AbstractText")
    if not abstract_nodes:
        raise ValueError("No abstract text found in the provided XML response")
        
    text_blocks: List[str] = []
    for node in abstract_nodes:
        # Join all text inside the element recursively, stripping out inline HTML tags automatically
        text = "".join(node.itertext()).strip()
        
        # Include label prefix if structured (e.g. OBJECTIVE: ...)
        label = node.attrib.get("Label")
        if label:
            text_blocks.append(f"{label}: {text}")
        else:
            text_blocks.append(text)
            
    return "\n".join(text_blocks)
