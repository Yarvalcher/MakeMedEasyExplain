import os
import re
from google.adk.agents.llm_agent import Agent
from google.adk.tools.agent_tool import AgentTool
from pathlib import Path
from MMEE_Agent.tools.openkb_loader import OKFIndexer
from MMEE_Agent.sub_agents.critic.agent import critic_agent
from MMEE_Agent.sub_agents.reviser.agent import reviser_agent
from MMEE_Agent.tools.validator import validate_analogy
from MMEE_Agent.tools.educator import check_anchoring_compliance

# Initialize local knowledge indexer pointing to the local knowledge base directory
local_kb_path = Path(__file__).parent.parent / "knowledge_base"
indexer = OKFIndexer(local_kb_path)

def save_to_knowledge_base(concept_id: str, layer: int, dependencies: list, content: str) -> str:
    """Saves a validated concept analogy to the local knowledge base as a Markdown file.
    
    Args:
        concept_id: Unique name for the concept (e.g. 't_cell', 'diabetes_type_1_vs_type_2').
        layer: Cognitive layer level (1-5).
        dependencies: List of related parent concepts.
        content: The validated metaphor/analogy body.
    """
    clean_id = re.sub(r'[^a-zA-Z0-9_]', '', concept_id.lower().strip().replace(" ", "_").replace("-", "_"))
    if not clean_id:
        return "Error: Invalid concept_id."
        
    target_dir = Path(__file__).parent.parent / "knowledge_base"
    target_file = target_dir / f"{clean_id}.md"
    
    # Path traversal security guardrail
    if not os.path.abspath(target_file).startswith(os.path.abspath(target_dir)):
        return "Security Violation: Access denied."
        
    # Format OKF v0.1 headers
    yaml_header = "---\n"
    yaml_header += f"concept_id: {clean_id}\n"
    yaml_header += f"layer: {layer}\n"
    yaml_header += "dependencies:\n"
    for dep in dependencies:
        yaml_header += f"  - {dep}\n"
    yaml_header += "---\n"
    
    full_text = yaml_header + content.strip() + "\n"
    
    try:
        os.makedirs(target_dir, exist_ok=True)
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(full_text)
        indexer.reload() # Reload local memory cache index
        return f"Saved to local wiki at knowledge_base/{clean_id}.md"
    except Exception as e:
        return f"Failed to save file: {e}"

def search_local_biology_textbook(query: str) -> str:
    """Searches the local OpenKB biology textbook index for foundational definitions.
    
    Args:
        query: The term or concept to look up (e.g., 'mhc_ii', 't_cell').
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

def run_scientific_and_educational_audit(analogy: str, abstract: str) -> str:
    """Audits the generated analogy for scientific correctness and concept anchoring compliance.
    
    Args:
        analogy: The generated visual analogy/explanation.
        abstract: The raw medical facts or abstract.
        
    Returns:
        A status string indicating whether the analogy is APPROVED or REJECTED with specific feedback.
    """
    # 1. Run scientific validation (medical advice & percentages)
    val_res = validate_analogy(analogy, abstract)
    if val_res["status"] == "REJECTED":
        return f"REJECTED: Scientific validation failed. Reason: {val_res['reasoning']}"
        
    # 2. Run educational anchoring verification
    anchoring_passed = check_anchoring_compliance(analogy)
    if not anchoring_passed:
        return "REJECTED: Educational validation failed. Reason: The analogy explains Layer 4/5 terms without anchoring them in familiar Layer 2/3 blocks."
        
    return "APPROVED: Analogy passed all scientific and educational validation gates."


# ==========================================
# 👑 Define Supervisor Agent (LLM Auditor)
# ==========================================

llm_auditor = Agent(
    model='gemini-2.5-flash',
    name='llm_auditor',
    description='MakeMedEasyExplain Supervisor Agent - democratizes medical literature.',
    instruction=(
        "You are the LLM Auditor (Supervisor). Your job is to coordinate the translation of complex medical queries into safe, simplified analogies.\n"
        "When a user asks a question:\n"
        "1. First call 'search_local_biology_textbook' to see if we already have the definition/facts stored locally.\n"
        "2. If the user provides a PubMed ID (PMID) or asks to search PubMed, OR if the concept is not found locally, call 'critic_agent' to query PubMed or search the web and establish the scientific truth.\n"
        "3. Pass the verified facts from 'critic_agent' directly to 'reviser_agent' to translate them into a simple, visual analogy.\n"
        "4. Once you receive the analogy, call 'run_scientific_and_educational_audit' to verify that the analogy is safe and complies with anchoring rules.\n"
        "5. If the audit is REJECTED, ask 'reviser_agent' to revise the analogy based on the feedback.\n"
        "6. If APPROVED, call 'save_to_knowledge_base' to save the validated analogy as a local Markdown file under the 'knowledge_base' folder (use a clean snake_case slug for the concept_id, layer=3, dependencies=[]).\n"
        "7. Present the final approved analogy clearly to the user, confirming that it has been saved to the wiki."
    ),
    tools=[
        AgentTool(agent=critic_agent),
        AgentTool(agent=reviser_agent),
        search_local_biology_textbook,
        run_scientific_and_educational_audit,
        save_to_knowledge_base
    ]
)

# Bind the llm_auditor as the entry point root_agent
root_agent = llm_auditor
