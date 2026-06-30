from google.adk.agents.llm_agent import Agent
from google.genai import types
from MMEE_Agent.tools.search_tool import web_search
from MMEE_Agent.tools.pubmed_tool import fetch_pubmed_abstract, extract_abstract_text, search_pubmed

def fetch_and_parse_pubmed_abstract(pmid: str) -> str:
    """Queries PubMed for a scientific paper's abstract using its PubMed ID (PMID).
    
    Args:
        pmid: The numerical ID of the PubMed article (e.g. '34351859').
    """
    try:
        raw_xml = fetch_pubmed_abstract(pmid)
        return extract_abstract_text(raw_xml)
    except Exception as e:
        return f"Error fetching abstract: {e}"

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
        "1. When given a query (whether a search keyword or a specific PubMed ID), use your tools ('web_search', 'fetch_and_parse_pubmed_abstract', or 'search_pubmed') to gather factual data.\n"
        "2. Synthesize these facts into a concise, technically accurate summary of the scientific truth.\n"
        "3. Do not simplify the language yet; keep it medically precise.\n"
        "4. CRITICAL CITATION RULE: If you retrieve data from PubMed (via keyword search or abstract fetch), you MUST explicitly include the PubMed ID (PMID: <PMID>) at the beginning or end of your output summary. This is mandatory for downstream verification."
    ),
    tools=[
        web_search,
        fetch_and_parse_pubmed_abstract,
        search_pubmed
    ]
)
