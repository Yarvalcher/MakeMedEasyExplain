# 🧬 MakeMedEasyExplain

### *Democratizing Primary Medical Literature via Governance-Aware, Multi-Agent Cognitive Scaffolding*

---

## 📋 1. Executive Summary & Problem Statement

### The Challenge

Every day, peer-reviewed medical discoveries are published on platforms like PubMed. However, this critical knowledge remains locked behind dense, clinical terminology (e.g., *MHC-II processing pathways, receptor-mediated cellular endocytosis*). Non-medical workers, patients, and healthcare students frequently face cognitive overload when attempting to read primary source texts.

This educational barrier creates a dangerous information vacuum, which is often filled by unscientific, unapproved, and misleading online medical rumors.

### The Solution

**MakeMedEasyExplain** is an autonomous, multi-agent AI system built on Google Cloud's Vertex AI Agent Platform (Tier 0). Its sole mission is to democratize primary medical literature by safely translating high-jargon scientific studies into structured, accessible, and visual analogies for the general public.

By grounding its reasoning strictly in verified repositories, utilizing a deterministic multi-agent pipeline, and employing an automated **Science-Proof Validation Loop**, the system programmatically intercepts and eliminates medical misinformation before it reaches the consumer.

---

## 🏛️ 2. Structural Vision: The 5-Layer Tree of Knowledge

To execute accurate translations without introducing factual errors, the system rejects arbitrary rewriting. Instead, it grounds its processing within a formalized **5-Layer Cognitive Abstraction Framework**, mapping the statistical distribution of public baseline understanding from visible physiology down to cellular transcription:

1. **Layer 1 (Empirical / ~99% Familiarity):** Visible, lived physical experience (e.g., arms, legs, localized pain).
2. **Layer 2 (Functional / ~85% Familiarity):** Basic bodily mechanics (e.g., processing food in the stomach, breaking a bone).
3. **Layer 3 (Macro-Anatomical / ~50% Familiarity):** Internal systems and major defenses (e.g., veins vs. arteries, general white blood cells).
4. **Layer 4 (Systemic Processes / ~20% Familiarity):** Invisible cellular coordination (e.g., T-Lymphocytes executing viral clearance, B-Lymphocytes producing antibodies).
5. **Layer 5 (Molecular / <5% Familiarity):** Deep abstraction frontiers (e.g., DNA transcription base pairs, chemical enzyme inhibitors).

The core technical strategy of MakeMedEasyExplain is **Concept Anchoring (Educational Scaffolding)**: the agent is programmatically forbidden from explaining an abstract Layer 4 or 5 concept using other Layer 4 or 5 terms. It must structurally anchor its analogies using Layer 2 or Layer 3 baseline structural blocks (metaphors like *lock and key, gates, soldiers, shields, factories, blueprints*) that the general public natively understands.

---

## 🧱 3. System Architecture & Technical Implementation

The system is constructed as a secure, deterministic, multi-agent pipeline that decouples non-deterministic AI reasoning from data extraction tools, preventing supervisor instruction drift.

```
       [User Interaction Interface (Flask Frontend)]
                             │
                             ▼
   [MakeMedEasyExplainPipeline (ADK SequentialAgent)]
                             │
       ┌─────────────────────┼─────────────────────┐
       ▼                     ▼                     ▼
[classifier_agent]  [fact_retriever]         [reviser_loop]
- Safety Check      - Local cache lookup     (LoopAgent, max_iters=3)
- Complexity/Layer  - PubMed MCP fallback    ├── [reviser_agent]
- Pydantic Metadata   (critic_agent audit)   └── [validator_agent]
                             │                     │
                             └──────────┬──────────┘
                                        ▼
                                  [saver_agent]
                                  - Citation parser
                                  - Write Lock guardrail
                                  - Syncs to GitHub
```

### Component Breakdown

* **The Ingestion & Caching Layer (OpenKB, OKF v0.1 & GitOps Sync):** Foundational medical biology textbooks are pre-processed using **OpenKB** into flat, cross-linked Markdown files backed by YAML frontmatter complying with the **Google Open Knowledge Format (OKF v0.1)**.
  
  To support a dynamic, growing wiki without incurring database storage costs or requiring container redeployments, the system implements a **GitOps-driven cloud cache**:
  * **Read Path**: The agent queries the local textbook directory first. If cached definitions exist, they are loaded instantly.
  * **Write Path**: When new topics are approved, the `SaveAgent` calls a GitHub API helper tool to push the new markdown file directly to the GitHub repository wiki.
  * **GitOps Startup Sync**: At application startup, a sync module pulls the latest files from the GitHub repository wiki to the local directory. During unit testing (`pytest` environment), this network/credential sync is conditionally bypassed to ensure zero-hanging and fast developer test cycles.
* **The Data Control Plane (PubMed & Web Search fallback):** When dynamic clinical research or general medical definitions are requested:
  * **PubMed Tool with Resilient Fallback**: The system queries the official **NCBI Entrez Programming Utilities (E-utilities) API** (using E-Search for indexing and E-Fetch for XML). If the PubMed API is rate-limited, unavailable, or fails, the tools (`search_pubmed_with_fallback` and `fetch_and_parse_pubmed_abstract`) catch the error and automatically fall back to executing a DuckDuckGo Lite search for the abstract or concept.
  * **Web Search Fallback**: For general queries and comparisons (e.g., *"difference between Hepatitis A, B, and C"*), the agent falls back to querying **DuckDuckGo Lite** via a dependency-free HTML parser tool to retrieve high-quality textbook snippets at $0.00 infrastructure cost.
* **Deterministic Orchestration Layer (Google ADK):** To prevent supervisor instruction drift, a parent `SequentialAgent` coordinates a structured linear chain:
  1. **`classifier_agent`**: Evaluates the safety and complexity of the query using a structured Pydantic `QueryMetadata` schema.
  2. **`FactRetrieverAgent`**: Searches local cached OpenKB definitions first, falling back to calling `critic_agent` to fetch PubMed abstracts and clinical facts.
  3. **`reviser_loop` (`LoopAgent`)**: Runs the `reviser_agent` (generator) and `ValidatorAgent` (audit gate) in a loop up to 3 times.
     - **Metaphor Generation**: The `reviser_agent` generates visual analogies anchored in Layer 2/3.
     - **Scientific & Educational Audit**: The `ValidatorAgent` runs regex-based checks for factual drift (hallucinations/mismatched percentages), prescriptive medical advice, and anchoring compliance. If it passes, it sets `is_approved = True` and escalates to break the loop. Otherwise, it sets `is_approved = False` and logs `audit_feedback` to guide the next iteration.
  4. **`SaveAgent`**: Parses PMID citations from the raw facts, appends them to the final analogy, and saves the file. If `is_approved` is `False` after 3 iterations, it blocks file saving and returns a user-friendly refusal message.

* **Callback-Based Safety Guardrails:**
  - **Pre-LLM Guardrail (`before_model_callback`)**: Registered on agent LLM calls to inspect query metadata. If `is_safe` is flagged `False` by the classifier, it intercepts execution and returns a clean refusal, avoiding downstream LLM invocation.
  - **Pre-Tool Guardrail (`before_tool_callback`)**: Validates that all arguments to write/save tools conform to security constraints (e.g., only saving `.md` files under the `knowledge_base/` folder and preventing path traversal `/` or `\\` characters), throwing errors before execution.

---

## 🎛️ 4. Deployment Environment & Financial Sustainability

### Tier 0 Compatibility & Budget Constraints

To guarantee a **$0.00 infrastructure cost structure** suitable for rapid independent developer prototyping, the system strictly adheres to the following constraints:
* **Budget Restriction:** All services utilized must result in a net cost of near $0.00. No paid cloud resources, premium database hosting, or expensive external indexing APIs may be used.
* **Model Routing:** The agents utilize `gemini-2.5-flash` via developer API configurations, taking advantage of high context allotments and strict built-in rate limits that prevent runaway costs.
* **Serverless Execution:** The application deployment is wrapped using Vertex AI’s `AgentEngineApp` template (Reasoning Engine environment) or deployed as a lightweight Docker container on Google Cloud Run. By binding the runtime to an `InMemoryArtifactService`, all operational trace payloads are held inside transient execution memory, eliminating the need for paid database servers.

---

## ☕ 5. Software Engineering Design Principles (SOLID, KISS, & DRY)

### SOLID Principles Alignment
* **Single Responsibility (SRP)**: Each agent does exactly one thing (e.g., `classifier_agent` classifies, `reviser_agent` simplifies, `ValidatorAgent` audits, and `SaveAgent` saves). XML parsing is isolated to a utility tool.
* **Open/Closed (OCP)**: Integrations use standardized MCP-like specifications. New search tools or databases can be registered without modifying core agent behaviors.
* **Liskov Substitution (LSP)**: All workers extend the base ADK `BaseAgent` class, making them cleanly interchangeable within Sequential or Loop orchestration structures.
* **Interface Segregation (ISP)**: Agents are only granted access to the specific tools they require (e.g., the generator reviser does not have direct access to search/write tools).
* **Dependency Inversion (DIP)**: High-level orchestration depends on abstract ADK agent structures, while data operations are abstracted behind dedicated tools.

### KISS (Keep It Simple, Stupid)
- Decouples data cache from complex databases by utilizing static Markdown files formatted with OKF v0.1 frontmatter.
- Uses Python's standard library for parsing and regex heuristics instead of heavy external dependencies, maintaining a lightweight runtime.

### DRY (Don't Repeat Yourself)
- Validation schemas, regex structures, and prompt templates are consolidated into unified global patterns imported across testing and production files.

---

## 🏆 6. Value Proposition & Evaluation Criteria Alignment

MakeMedEasyExplain achieves high alignment with the Kaggle Capstone judging dimensions across all scoring fields:

1. **Core Concept & Value (Agents for Good track):** It actively applies AI technology to a critical human health challenge, translating complex academic literature to maximize accessibility and combat misinformation.
2. **Sophisticated Solution Design:** It moves away from fragile, single-prompt chat interactions. Instead, it features a clear multi-agent architecture with localized vector-equivalent lookups, custom tools, and strict automated validation guardrails.
3. **Flagship Google Stack Proficiency:** The codebase directly implements modern 2026 AI engineering patterns, cleanly unifying the **Google ADK, Model Context Protocol (MCP) tool design patterns, Open Knowledge Format (OKF v0.1) documentation layouts, and Vertex AI Reasoning Engine deployment standards**.

---

## 📂 7. Project Documentation Index
* [Tasks & Status](file:///c:/Users/yaros/Documents/PortfolioProjects/mademedeasyexplain/MakeMedEasyExplain/docs/tasks.md)
* [Software Engineering Design Review](file:///c:/Users/yaros/Documents/PortfolioProjects/mademedeasyexplain/MakeMedEasyExplain/docs/design_review.md)
