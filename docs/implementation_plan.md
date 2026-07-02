# Implementation Plan: Orchestration Re-architecting & Guardrails

We are refactoring the **MakeMedEasyExplain** core agent architecture. Instead of an LLM-instruction-driven Supervisor coordinating all agents dynamically (which is prone to instruction drift), we will implement a deterministic ADK **SequentialAgent + LoopAgent** pipeline structure and integrate **Callback-based Guardrails**.

---

## Current Solution vs. Next Stages Comparison

| Aspect | Current Solution (`agent.py`, `README.md`) | Proposed Next Stage (Sequential/Loop Workflows & Guardrails) |
| :--- | :--- | :--- |
| **Orchestration** | Single `llm_auditor` Supervisor agent routing via LLM instructions and tool calls. | A parent `SequentialAgent` orchestrating a clear linear chain: `[ClassifierAgent, LocalKB/Critic/Reviser, LoopAgent(Reviser + Audit), SaveToKB]`. |
| **Classification** | Done implicitly via the Supervisor's prompt instructions. | A dedicated structured `classifier_agent` using a Pydantic schema to extract layer, complexity, safety, and core concepts. |
| **Safety Guardrails** | Simple check inside Flask `app.py` after the entire pipeline runs. | 1. Pre-LLM safety check embedded in `before_model_callback` for the supervisor/classifier.<br>2. Parameter/Extension validation lock inside `before_tool_callback` for tool calls (e.g. `save_to_knowledge_base`). |
| **Refinement Loop** | Dynamic LLM instructions asking the supervisor to retry if the validator rejects the analogy. | A code-defined `LoopAgent` that runs `[Reviser, Audit]` up to 3 times, ending early via a Stop Checker when approved. |

---

## Proposed Changes

### 1. Dedicated Query Classifier Agent (`classifier_agent`)
We will create a structured Pydantic schema for classification metadata:
```python
from pydantic import BaseModel, Field

class QueryMetadata(BaseModel):
    is_safe: bool = Field(description="False if the query involves inappropriate content, self-harm, diagnostic requests, or unsafe/off-topic themes.")
    safety_reason: str = Field(description="Reason for safety rejection, or empty if safe.")
    is_complex: bool = Field(description="True if the concept involves complex Layer 4/5 cellular or molecular jargon requiring analogy simplification.")
    estimated_layer: int = Field(description="Estimated layer (1-5) matching the MakeMedEasyExplain cognitive model.")
    core_concept: str = Field(description="The sanitized name of the core biological concept.")
```

### 2. Pre-LLM and Pre-Tool Callback Guardrails
- **Pre-LLM Guardrail (`before_model_callback`)**: Registers a callback on the LLM calls to quickly intercept safety violations. If `is_safe` is false, it returns an `LlmResponse` with a clean refusal explanation, avoiding downstream LLM invocation.
- **Pre-Tool Guardrail (`before_tool_callback`)**: Validates that all arguments to write/save tools conform to security constraints (e.g. only saving `.md` files under the `knowledge_base/` folder), throwing errors before tool execution.

### 3. Pipeline Re-architecting (Sequential & Loop Agents)
We will structure the root agent as a custom `SequentialAgent` containing:
1. `classifier_agent` (evaluates input query and populates session state).
2. `fact_retriever_agent` (runs local search or `critic_agent` to fetch raw PubMed abstracts/facts).
3. `reviser_loop` (`LoopAgent` running the generator `reviser_agent` and critic validator).
4. `save_agent` (saves approved concepts to the local knowledge base).

---

## Verification Plan

### Automated Tests
- Implement new TDD tests in [test_classifier.py](file:///c:/Users/yaros/Documents/PortfolioProjects/mademedeasyexplain/MakeMedEasyExplain/tests/unit/test_classifier.py) and [test_guardrails.py](file:///c:/Users/yaros/Documents/PortfolioProjects/mademedeasyexplain/MakeMedEasyExplain/tests/unit/test_guardrails.py).
- Verify all unit and integration tests run successfully:
  ```powershell
  uv run pytest
  ```
