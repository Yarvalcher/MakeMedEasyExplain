# 🧠 Obsidian Knowledge Graph Integration Ideation

## 1. Problem Statement
As the MakeMedEasyExplain system dynamically generates simplified analogies and commits them directly to the `knowledge_base/` via GitOps, the number of files will grow. It becomes difficult to visualize:
- The cognitive connections between different medical concepts (e.g., how `t_cell_activation` connects to `immune_system`).
- The mapping between cognitive abstraction layers (e.g., confirming that Layer 4/5 concepts are correctly anchored to Layer 2/3 concepts).

---

## 2. Proposed Solution
Use **Obsidian** (a local Markdown vault viewer) to automatically visualize the knowledge base as a dynamic network graph. 

Because the knowledge base consists of flat Markdown files matching the **Google Open Knowledge Format (OKF v0.1)**, a developer or user can simply open the `knowledge_base/` directory as an Obsidian Vault.

To enable Obsidian to draw connection lines between concepts automatically:
1. Parse the `dependencies` list supplied to the `SaveAgent` at the end of the pipeline.
2. In `save_to_knowledge_base`, format each dependency as a standard Wiki-link: `[[dependency_id]]`.
3. Append these wiki-links to the bottom of the generated markdown file under a `## 🔗 Related Concepts` section.

### Example Markdown Format Output:
```markdown
---
concept_id: heart_function
layer: 2
dependencies:
  - cardiovascular_system
---
# Як Працює Серце

Уявіть серце як потужний, невтомний двигун...

---
## 🔗 Related Concepts
* [[cardiovascular_system]]
```

---

## 3. Implementation Plan

### Step 3.1: Modify `save_to_knowledge_base`
Update the write utility in `MMEE_Agent/agent.py` to compile dependency list elements:
```python
    # Format Obsidian links
    if dependencies:
        full_text += "\n---\n## 🔗 Related Concepts\n"
        for dep in dependencies:
            clean_dep = re.sub(r'[^a-zA-Z0-9_]', '', dep.lower().strip().replace(" ", "_").replace("-", "_"))
            full_text += f"- [[{clean_dep}]]\n"
```

### Step 3.2: Verification
1. Create a dummy analogy using the test app with dependencies specified.
2. Verify that the output markdown contains the formatted Wiki-links at the bottom.
3. Open the folder in Obsidian and view the node-link graph visualization.
