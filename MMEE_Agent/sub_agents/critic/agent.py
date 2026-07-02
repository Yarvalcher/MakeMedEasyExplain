from google.adk.agents.llm_agent import Agent
from google.genai import types
from MMEE_Agent.tools.search_tool import web_search
from MMEE_Agent.tools.pubmed_tool import fetch_pubmed_abstract, extract_abstract_text, search_pubmed

def fetch_and_parse_pubmed_abstract(pmid: str) -> str:
    """Queries PubMed for a scientific paper's abstract using its PubMed ID (PMID).
    If PubMed queries fail due to rate limits or network issues, it automatically
    falls back to a web search query for the PMID abstract.
    
    Args:
        pmid: The numerical ID of the PubMed article (e.g. '34351859').
    """
    try:
        raw_xml = fetch_pubmed_abstract(pmid)
        return extract_abstract_text(raw_xml)
    except Exception as e:
        fallback_query = f"PubMed PMID {pmid} abstract"
        fallback_results = web_search(fallback_query)
        return f"PubMed fetch failed ({e}). Falling back to web search results for PMID {pmid}:\n\n{fallback_results}"

def search_pubmed_with_fallback(query: str) -> str:
    """Searches PubMed for articles matching the query term. 
    If PubMed is rate limited or unavailable, it automatically falls back to web search.
    
    Args:
        query: The search term or keywords (e.g. 'Hepatitis A').
    """
    try:
        pmids = search_pubmed(query)
        if pmids:
            return f"Found PubMed articles with PMIDs: {', '.join(pmids)}"
        else:
            fallback_results = web_search(query)
            return f"No PMIDs found on PubMed for query: '{query}'. Falling back to web search:\n\n{fallback_results}"
    except Exception as e:
        fallback_results = web_search(query)
        return f"PubMed search failed ({e}). Falling back to web search for '{query}':\n\n{fallback_results}"

critic_agent = Agent(
    model='gemini-2.5-flash',
    name='critic_agent',
    description='Gathers scientific truth by fetching PubMed articles by ID (PMID), searching PubMed by keywords, or searching the web.',
    generate_content_config=types.GenerateContentConfig(
        http_options=types.HttpOptions(
            retry_options=types.HttpRetryOptions(initial_delay=1.0, attempts=3)
        )
    ),
    instruction=(
        "You are the Critic Agent. Your job is to verify medical and scientific claims.\n"
        "1. When given a query (whether a search keyword or a specific PubMed ID), use your tools ('web_search', 'fetch_and_parse_pubmed_abstract', or 'search_pubmed_with_fallback') to gather factual data.\n"
        "2. Synthesize these facts into a concise, technically accurate summary of the scientific truth.\n"
        "3. Do not simplify the language yet; keep it medically precise.\n"
        "4. CRITICAL CITATION RULE: If you retrieve data from PubMed (via keyword search or abstract fetch), you MUST explicitly include the PubMed ID (PMID: <PMID>) at the beginning or end of your output summary. This is mandatory for downstream verification.\n"
        "5. If a tool reports that PubMed failed and fell back to web search, utilize the provided web search facts but clearly note that a fallback search was used."
    ),
    tools=[
        web_search,
        fetch_and_parse_pubmed_abstract,
        search_pubmed_with_fallback
    ]
)
