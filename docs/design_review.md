# Software Engineering Design Review: SOLID, KISS, & DRY

This document evaluates the architectural design of **MakeMedEasyExplain** against foundational software engineering principles to ensure maintainability, testability, and operational simplicity.

---

## ☕ 1. SOLID Principles Alignment

### 🎯 Single Responsibility Principle (SRP)
*Each component or module must have exactly one reason to change.*
*   **Separation of Agent Concerns**:
    *   `mmee_supervisor`: Manages user session state and coordinates orchestration. It does not contain prompt logic or translation heuristics.
    *   `simplification_educator`: Focused entirely on metaphor generation, vocabulary translation, and cognitive layer compliance.
    *   `science_proof_validator`: Responsible solely for checking correctness, enforcing schema validation, and preventing prescriptive medical advice.
*   **Decoupled Parsers**: XML parsing (parsing PubMed data via `ElementTree`) is isolated to a dedicated tool, preventing HTML/XML cleanup code from polluting core agent logic.

### 🔌 Open/Closed Principle (OCP)
*Software entities should be open for extension, but closed for modification.*
*   **MCP (Model Context Protocol) Integration**: The PubMed integration uses the standardized MCP specification. If the system needs to expand to retrieve documents from arXiv, Cochrane Reviews, or a local vector database, a new MCP tool can be added without modifying the core agent logic.
*   **Cognitive Layer Extensibility**: The 5-Layer Cognitive Abstraction Framework is designed as a mapping system. Adding intermediate sub-layers or customizing layer thresholds can be done by adjusting the layout definitions without redesigning the simplification agents.

### 📐 Liskov Substitution Principle (LSP)
*Subtypes must be substitutable for their base types.*
*   **Standardized Agent Interfaces**: The workers (Educator, Validator) share a common agent base class from the Google ADK. The Supervisor executes them interchangeably within the orchestration runner without knowing their internal reasoning configurations.
*   **Tool Schema Compliance**: All query interfaces conform to the same function-calling interfaces, making local and remote document resolvers interchangeable.

### 🧹 Interface Segregation Principle (ISP)
*Clients should not be forced to depend on interfaces they do not use.*
*   **Minimal Tool Exposure**: Workers only receive access to the specific tools they require. For example, the `science_proof_validator` does not have access to the PubMed API tool or local files; it only receives the outputs of the Educator and the raw abstract, minimizing security risk and prompt pollution.

### 🏗️ Dependency Inversion Principle (DIP)
*High-level modules should not depend on low-level modules; both should depend on abstractions.*
*   **Orchestration Decoupling**: The Supervisor routes tasks using abstract agent roles rather than hardcoded concrete class implementations.
*   **Data Access Layer**: Rather than making direct REST calls within agent prompts, data operations are abstracted behind tools (OpenKB retrieval and PubMed MCP).

---

## 🧠 2. KISS (Keep It Simple, Stupid) Alignment

*   **Flat File Architecture & GitOps Raw CDN (OpenKB)**: Instead of requiring an active, paid database cluster (e.g. Pinecone, PostgreSQL with pgvector) for foundational knowledge, the system uses static Markdown files with YAML frontmatter. By using the GitHub Raw CDN as the read path and committing directly to the repo via API on the write path (restricted by strict path and extension validator guardrails), the database remains entirely serverless, version-controlled, and costs $0.00.
*   **Standard Library XML Parsing**: Instead of adding heavy external dependencies (e.g., BeautifulSoup, lxml), the system extracts the targeted `<AbstractText>` using Python’s native `xml.etree.ElementTree` parser.
*   **Serverless Tier 0 Runtime**: Deployment avoids complex Kubernetes orchestrations or persistent VMs. By leveraging Vertex AI's Reasoning Engine (`InMemoryArtifactService`), the runtime remains entirely stateless and manages operational tracing in transient memory.

---

## 🔁 3. DRY (Don't Repeat Yourself) Alignment

*   **Unified Schema Enforcement**: Prompt schemas, safety validation schemas, and API response structures are defined once in global validation templates or Pydantic models. They are imported by both the Educator (to structure its responses) and the Validator (to parse them).
*   **Consolidated Ingestion Utilities**: The logic for sanitizing clinical vocabulary is implemented in a shared preprocessing utility module, preventing the repetition of string-cleaning code across different tools.
