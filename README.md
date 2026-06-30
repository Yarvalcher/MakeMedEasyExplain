# 🧬 MakeMedEasyExplain

### *Democratizing Primary Medical Literature via Governance-Aware, Multi-Agent Cognitive Scaffolding*

MakeMedEasyExplain is an autonomous, multi-agent AI system built on Google Cloud's Vertex AI Agent Platform (Tier 0). Its sole mission is to democratize primary medical literature by safely translating high-jargon scientific studies into structured, accessible, and visual analogies for the general public.

---

## 📖 Table of Contents
* [1. Executive Summary & Problem Statement](#-1-executive-summary--problem-statement)
* [2. Structural Vision: The 5-Layer Tree of Knowledge](#-2-structural-vision-the-5-layer-tree-of-knowledge)
* [3. System Architecture & Technical Implementation](#-3-system-architecture--technical-implementation)
* [4. Deployment Environment & Financial Sustainability](#-4-deployment-environment--financial-safety)
* [5. Getting Started & Local Development](#-5-getting-started--local-development)
* [6. Running Tests](#-6-running-tests)
* [7. Project Documentation Index](#-7-project-documentation-index)

---

## 📋 1. Executive Summary & Problem Statement
Every day, peer-reviewed medical discoveries are published on platforms like PubMed. However, this critical knowledge remains locked behind dense, clinical terminology. Non-medical workers, patients, and healthcare students frequently face cognitive overload.

**MakeMedEasyExplain** grounds its reasoning strictly in verified repositories and employs an automated **Science-Proof Validation Loop** to programmatically intercept and eliminate medical misinformation before it reaches the consumer.

---

## 🏛️ 2. Structural Vision: The 5-Layer Tree of Knowledge
To execute accurate translations without introducing factual errors, the system grounds its processing within a formalized **5-Layer Cognitive Abstraction Framework**:
1. **Layer 1 (Empirical / ~99% Familiarity):** Visible, lived physical experience (e.g., arms, legs).
2. **Layer 2 (Functional / ~85% Familiarity):** Basic bodily mechanics (e.g., processing food in stomach).
3. **Layer 3 (Macro-Anatomical / ~50% Familiarity):** Internal systems (e.g., veins vs. arteries, general white blood cells).
4. **Layer 4 (Systemic Processes / ~20% Familiarity):** Invisible cellular coordination (e.g., T-Lymphocytes executing viral clearance).
5. **Layer 5 (Molecular / <5% Familiarity):** Deep abstraction frontiers (e.g., DNA transcription base pairs, chemical enzyme inhibitors).

**Concept Anchoring Rule:** The agent is programmatically forbidden from explaining an abstract Layer 4 or 5 concept using other Layer 4 or 5 terms. It must structurally anchor its analogies using Layer 2 or Layer 3 baseline concepts.

---

## 🧱 3. System Architecture & Technical Implementation
* **The Ingestion & Caching Layer (OpenKB, OKF v0.1 & GitOps Raw CDN):** Reads cached textbook definitions directly from the GitHub Raw CDN, caching new approved explanations locally at runtime.
* **The Data Control Plane (PubMed & Web Search fallback):** Fetches dynamic facts from PubMed API (E-utilities) or DuckDuckGo Lite (fallback) using dependency-free, standard library parsing.
* **The Multi-Agent Orchestration Layer (Google ADK)**: Hierarchical agent team using native `AgentTool` delegation:
  * `llm_auditor` (Supervisor): Coordinates the pipeline, runs validation gates, and caches approved analogies.
  * `critic_agent` (Worker): Gathers and audits facts using web and PubMed search tools to establish "scientific truth".
  * `reviser_agent` (Worker): Translates complex medical facts into simplified visual analogies.

### 📂 3.1 Refactored Package Structure
The codebase isolates sub-agents and tool libraries into structured folders for maximum modularity and scalability:
```text
MMEE_Agent/
├── agent.py               # Root Entry Point (llm_auditor supervisor configuration)
├── sub_agents/            # Agent Configuration Folder
│   ├── critic/
│   │   └── agent.py       # critic_agent (connected to search & PubMed tools)
│   └── reviser/
│       └── agent.py       # reviser_agent (simplification educator)
└── tools/                 # Standalone Tool Utilities Folder
    ├── educator.py        # concept anchoring & layer maps checks
    ├── openkb_loader.py   # local OpenKB textbook indexer
    ├── pubmed_tool.py     # PubMed API E-utilities fetchers
    ├── search_tool.py     # DuckDuckGo Lite free scraping search
    └── validator.py       # factual drift & safety audit gates
```

---

## 🎛️ 4. Deployment Environment & Financial Safety
* **Model Routing**: Utilizes `gemini-2.5-flash` or `gemini-3.5-flash` via free developer APIs.
* **Serverless Execution**: Runs on Vertex AI `AgentEngineApp` using `InMemoryArtifactService` to maintain a $0.00 infrastructure cost structure.

---

## 🚀 5. Getting Started & Local Development

### Prerequisites
* Python 3.11+
* `uv` for python dependency and environment management
* Google Cloud CLI (`gcloud`)

### Quickstart Setup
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Yarvalcher/MakeMedEasyExplain.git
   cd MakeMedEasyExplain
   ```

2. **Create & Activate Environment**:
   ```bash
   uv venv
   .venv\Scripts\activate.ps1  # Windows PowerShell
   ```

3. **Install Dependencies**:
   ```bash
   uv pip install -r requirements.txt
   ```

4. **Verify ADK Installation**:
   ```bash
   adk --help
   ```

5. **Run the Agent (Web UI)**:
   Launch the interactive local web interface:
   ```bash
   .venv\Scripts\adk web --port 8000 MMEE_Agent
   ```
   Once started, open your browser and navigate to `http://127.0.0.1:8000` to interact with the agent.

---

## 🧪 6. Running Tests
The project relies on Test-Driven Development (TDD). 

To run the complete test suite (unit and integration tests):
```bash
uv run pytest
```
To run only unit tests:
```bash
uv run pytest tests/unit
```
To run the live PubMed integration test:
```bash
uv run pytest tests/integration
```

---

## 📂 7. Project Documentation Index
* [Project Idea / Overview](file:///c:/Users/yaros/Documents/PortfolioProjects/mademedeasyexplain/MakeMedEasyExplain/docs/project_idea.md)
* [Decomposed Implementation Phases & Tasks](file:///c:/Users/yaros/Documents/PortfolioProjects/mademedeasyexplain/MakeMedEasyExplain/docs/tasks.md)
* [Software Engineering Design Review](file:///c:/Users/yaros/Documents/PortfolioProjects/mademedeasyexplain/MakeMedEasyExplain/docs/design_review.md)
* [License (MIT)](file:///c:/Users/yaros/Documents/PortfolioProjects/mademedeasyexplain/MakeMedEasyExplain/LICENSE)
