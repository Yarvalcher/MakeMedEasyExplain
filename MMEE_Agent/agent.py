from google.adk.agents.llm_agent import Agent
from pathlib import Path
from MMEE_Agent.pubmed_tool import fetch_pubmed_abstract, extract_abstract_text, search_pubmed
from MMEE_Agent.openkb_loader import OKFIndexer
from MMEE_Agent.orchestrator import run_orchestration_loop

# Initialize local knowledge indexer pointing to the local knowledge base directory
local_kb_path = Path(__file__).parent.parent / "knowledge_base"
indexer = OKFIndexer(local_kb_path)

def fetch_and_parse_pubmed_abstract(pmid: str) -> str:
    """Queries PubMed for a scientific paper's abstract using its PubMed ID (PMID).
    
    Args:
        pmid: The numerical ID of the PubMed article (e.g. '34351859').
        
    Returns:
        The extracted abstract plain text.
    """
    try:
        raw_xml = fetch_pubmed_abstract(pmid)
        return extract_abstract_text(raw_xml)
    except Exception as e:
        return f"Error fetching abstract: {e}"

def generate_validated_analogy(abstract: str) -> str:
    """Translates a raw scientific abstract into a plain-language, visual analogy.
    
    This function runs the supervisor-worker orchestration loop, passing the simplified
    analogy to the Science-Proof Validator to ensure no prescriptive advice is given
    and no factual drift/hallucination is introduced.
    
    Args:
        abstract: The raw clinical text abstract to simplify.
        
    Returns:
        The validated safe analogy.
    """
    try:
        result = run_orchestration_loop(abstract, max_retries=3)
        if result["status"] == "APPROVED":
            return result["analogy"]
        else:
            return f"Validation failed: {result['reasoning']}\n\nLast generated analogy:\n{result['analogy']}"
    except Exception as e:
        return f"Error during simplification: {e}"

def search_local_biology_textbook(query: str) -> str:
    """Searches the local OpenKB biology textbook index for foundational definitions.
    
    Args:
        query: The term or concept to look up (e.g., 'mhc_ii', 't_cell').
        
    Returns:
        A list of matching concepts with their layers, dependencies, and descriptions.
    """
    try:
        docs = indexer.search(query)
        if not docs:
            return f"No results found in the local knowledge base for query '{query}'."
        
        output = []
        for doc in docs:
            output.append(
                f"Concept: {doc.concept_id}\n"
                f"Cognitive Layer: {doc.layer}\n"
                f"Dependencies: {', '.join(doc.dependencies)}\n"
                f"Description: {doc.body.strip()}\n"
                f"---"
            )
        return "\n\n".join(output)
    except Exception as e:
        return f"Error searching local knowledge base: {e}"

def search_and_explain_pubmed(query: str) -> str:
    """Searches PubMed for a medical topic (e.g., 'Hepatitis'), fetches the top match, and returns a simplified analogy.
    
    Args:
        query: The medical topic or keywords to search for.
        
    Returns:
        The validated analogy for the top matching article.
    """
    try:
        pmids = search_pubmed(query, max_results=1)
        if not pmids:
            return f"No PubMed articles found for query '{query}'."
        pmid = pmids[0]
        abstract = fetch_and_parse_pubmed_abstract(pmid)
        analogy = generate_validated_analogy(abstract)
        return f"Top PubMed Match (PMID: {pmid}):\n\n{analogy}"
    except Exception as e:
        return f"Error searching and simplifying: {e}"


# Define the root Supervisor Agent
root_agent = Agent(
    model='gemini-2.5-flash',
    name='MMEE_Agent',
    description='MakeMedEasyExplain Supervisor Agent - democratizes medical literature.',
    instruction=(
        "You are the central router for MakeMedEasyExplain. Your job is to help users understand complex medical literature.\n"
        "1. If the user provides a PubMed ID (PMID), fetch it using 'fetch_and_parse_pubmed_abstract'.\n"
        "2. If they ask about a general medical topic (e.g. Hepatitis, Diabetes, receptor pathways) instead of a specific PMID, search for it using 'search_and_explain_pubmed'.\n"
        "3. Once you have a raw abstract (either fetched or entered directly), translate it using 'generate_validated_analogy'.\n"
        "4. If they ask for basic textbook definitions (e.g., cell, receptor, mhc_ii), look them up in the local files using 'search_local_biology_textbook'.\n"
        "Always present the simplified analogies clearly to the user."
    ),
    tools=[
        fetch_and_parse_pubmed_abstract,
        generate_validated_analogy,
        search_local_biology_textbook,
        search_and_explain_pubmed
    ]
)
