import os
import re
import json
from typing import AsyncGenerator, Optional, Dict, Any
from pathlib import Path

from google.adk.agents import BaseAgent, SequentialAgent, LoopAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.tools.agent_tool import AgentTool

from MMEE_Agent.tools.openkb_loader import OKFIndexer
from MMEE_Agent.sub_agents.classifier.agent import classifier_agent, QueryMetadata
from MMEE_Agent.sub_agents.critic.agent import critic_agent
from MMEE_Agent.sub_agents.reviser.agent import reviser_agent
from MMEE_Agent.tools.validator import validate_analogy
from MMEE_Agent.tools.educator import check_anchoring_compliance

# Initialize local knowledge indexer pointing to the local knowledge base directory
local_kb_path = Path(__file__).parent.parent / "knowledge_base"
indexer = OKFIndexer(local_kb_path)

def save_to_knowledge_base(concept_id: str, layer: int, dependencies: list, content: str) -> str:
    """Saves a validated concept analogy to the local knowledge base as a Markdown file."""
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
    """Searches the local OpenKB biology textbook index for foundational definitions."""
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
    """Audits the generated analogy for scientific correctness and concept anchoring compliance."""
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
# 🛡️ Callback-Based Guardrails
# ==========================================

from google.genai import types

def before_model_guardrail(
    callback_context: CallbackContext, 
    llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """Pre-LLM guardrail to block requests that fail safety checks."""
    state = callback_context.session.state
    metadata = state.get("query_metadata")
    if metadata:
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except Exception:
                pass
        
        is_safe = True
        reason = "Request blocked due to safety guidelines."
        if isinstance(metadata, dict):
            is_safe = metadata.get("is_safe", True)
            reason = metadata.get("safety_reason", reason)
        elif hasattr(metadata, "is_safe"):
            is_safe = metadata.is_safe
            reason = getattr(metadata, "safety_reason", reason)
            
        if not is_safe:
            return LlmResponse(content=types.Content(parts=[types.Part.from_text(text=f"Request blocked: {reason}")]))
            
    return None

def before_tool_guardrail(tool: Any, args: Dict[str, Any], tool_context: Any) -> Optional[Dict]:
    """Pre-tool guardrail to check tool arguments (e.g. path traversal check)."""
    if tool.name == "save_to_knowledge_base":
        concept_id = args.get("concept_id", "")
        # Prevent traversal or malicious inputs
        clean_id = re.sub(r'[^a-zA-Z0-9_]', '', concept_id.lower().strip().replace(" ", "_").replace("-", "_"))
        if not clean_id or ".." in concept_id or "/" in concept_id or "\\" in concept_id:
            return {"error": "Security Violation: Path traversal or invalid characters detected."}
    return None


# ==========================================
# 🤖 Custom Pipeline Agents
# ==========================================

class FactRetrieverAgent(BaseAgent):
    """Retrieves facts locally or runs critic_agent to fetch clinical research."""
    
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        metadata = ctx.session.state.get("query_metadata")
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except Exception:
                pass
                
        if not metadata:
            yield Event(author=self.name, content=types.Content(parts=[types.Part.from_text(text="Error: No query metadata found.")]))
            ctx.end_invocation = True
            return
            
        is_safe = True
        reason = "Inappropriate content."
        if isinstance(metadata, dict):
            is_safe = metadata.get("is_safe", True)
            reason = metadata.get("safety_reason", reason)
        elif hasattr(metadata, "is_safe"):
            is_safe = metadata.is_safe
            reason = getattr(metadata, "safety_reason", reason)
            
        if not is_safe:
            yield Event(author=self.name, content=types.Content(parts=[types.Part.from_text(text=f"Request blocked: {reason}")]))
            ctx.end_invocation = True
            return
            
        # Extract metadata fields
        is_complex = metadata.get("is_complex", True) if isinstance(metadata, dict) else getattr(metadata, "is_complex", True)
        concept_id = metadata.get("core_concept", "concept") if isinstance(metadata, dict) else getattr(metadata, "core_concept", "concept")
        
        # Get query
        query = ""
        if ctx.session.history:
            for msg in reversed(ctx.session.history):
                if msg.role == "user":
                    query = msg.parts[0].text
                    break
        if not query:
            query = concept_id

        # 1. Check local knowledge base first
        local_result = search_local_biology_textbook(concept_id)
        if "No results found" not in local_result:
            ctx.session.state["raw_facts"] = local_result
            ctx.session.state["is_cached"] = True
            yield Event(author=self.name, content=types.Content(parts=[types.Part.from_text(text=local_result)]))
            ctx.end_invocation = True
            return
            
        # Initialize loop variables
        ctx.session.state["is_cached"] = False
        ctx.session.state["audit_feedback"] = ""
        
        # 2. Fetch facts using critic_agent
        yield Event(author=self.name, content=types.Content(parts=[types.Part.from_text(text=f"Retrieving online medical research for '{concept_id}'...")]))
        
        # Call critic_agent programmatically
        raw_facts = ""
        async for event in critic_agent.run_async(ctx):
            if event.content:
                raw_facts += event.content
                yield event
                
        ctx.session.state["raw_facts"] = raw_facts
        
        # 3. If simple (Layer 1-3) and not cached, proceed without ending early so the reviser can simplify it
        if not is_complex:
            pass


class ValidatorAgent(BaseAgent):
    """Validator step inside the LoopAgent. Escales if approved, otherwise saves feedback."""
    
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        metadata = ctx.session.state.get("query_metadata")
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except Exception:
                pass
                
        is_complex = True
        if isinstance(metadata, dict):
            is_complex = metadata.get("is_complex", True)
        elif hasattr(metadata, "is_complex"):
            is_complex = metadata.is_complex

        if not is_complex:
            # Simple concept: auto-approve immediately
            yield Event(author=self.name, content=types.Content(parts=[types.Part.from_text(text="APPROVED: Simple concept bypassed validation.")]))
            yield Event(author=self.name, actions=EventActions(escalate=True))
            return

        analogy = ctx.session.state.get("analogy", "")
        raw_facts = ctx.session.state.get("raw_facts", "")
        
        audit_res = run_scientific_and_educational_audit(analogy, raw_facts)
        yield Event(author=self.name, content=types.Content(parts=[types.Part.from_text(text=audit_res)]))
        
        if "APPROVED" in audit_res:
            yield Event(author=self.name, actions=EventActions(escalate=True))
        else:
            ctx.session.state["audit_feedback"] = audit_res


class SaveAgent(BaseAgent):
    """Saves approved analogies to knowledge base and formats final response."""
    
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        metadata = ctx.session.state.get("query_metadata")
        analogy = ctx.session.state.get("analogy", "")
        raw_facts = ctx.session.state.get("raw_facts", "")
        
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except Exception:
                pass
                
        concept_id = metadata.get("core_concept", "concept") if isinstance(metadata, dict) else getattr(metadata, "core_concept", "concept")
        layer = metadata.get("estimated_layer", 4) if isinstance(metadata, dict) else getattr(metadata, "estimated_layer", 4)
        
        # Parse PMID from raw_facts to append citation
        pmid_match = re.search(r'PMID:\s*(\d+)', raw_facts, re.IGNORECASE)
        citation = ""
        if pmid_match:
            pmid = pmid_match.group(1)
            citation = f"\n\nSource: [PubMed ID: {pmid}](https://pubmed.ncbi.nlm.nih.gov/{pmid}/)"
            
        final_analogy = analogy + citation
        ctx.session.state["analogy"] = final_analogy
        
        save_msg = save_to_knowledge_base(concept_id, layer, [], final_analogy)
        yield Event(author=self.name, content=types.Content(parts=[types.Part.from_text(text=f"{final_analogy}\n\n* {save_msg}")]))


# Register callbacks on sub-agents to intercept safety violations & block calls
classifier_agent.before_model_callback = before_model_guardrail
reviser_agent.before_model_callback = before_model_guardrail
critic_agent.before_model_callback = before_model_guardrail

# Register callbacks for tools
critic_agent.before_tool_callback = before_tool_guardrail


# ==========================================
# 👑 Define Parent SequentialAgent Pipeline
# ==========================================

root_agent = SequentialAgent(
    name="MakeMedEasyExplainPipeline",
    sub_agents=[
        classifier_agent,
        FactRetrieverAgent(name="fact_retriever"),
        LoopAgent(
            name="reviser_loop",
            max_iterations=3,
            sub_agents=[
                reviser_agent,
                ValidatorAgent(name="validator")
            ]
        ),
        SaveAgent(name="saver")
    ]
)
