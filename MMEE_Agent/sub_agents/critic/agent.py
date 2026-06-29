from google.adk.agents.llm_agent import Agent
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
    description='Gathers and audits medical statements to establish scientific truth.',
    instruction=(
        "You are the Critic Agent. Your job is to verify medical and scientific claims.\n"
        "1. When given a query, use the 'google_search' tool (web_search) or 'fetch_and_parse_pubmed_abstract' to gather factual data.\n"
        "2. Synthesize these facts into a concise, technically accurate summary of the scientific truth.\n"
        "3. Do not simplify the language yet; keep it medically precise."
    ),
    tools=[
        web_search,
        fetch_and_parse_pubmed_abstract,
        search_pubmed
    ]
)
