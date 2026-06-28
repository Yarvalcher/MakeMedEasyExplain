import pytest
from pathlib import Path
from MMEE_Agent.openkb_loader import parse_okf_file, OKFDocument

def test_parse_valid_okf_file(tmp_path: Path):
    # Create a dummy OKF v0.1 file
    content = """---
concept_id: mhc_ii
layer: 4
dependencies:
  - receptor_mediated_endocytosis
---
MHC-II processing pathways are crucial for presenting antigens.
"""
    file_path = tmp_path / "mhc_ii.md"
    file_path.write_text(content, encoding="utf-8")

    # Run parser
    doc = parse_okf_file(file_path)

    # Assertions
    assert isinstance(doc, OKFDocument)
    assert doc.concept_id == "mhc_ii"
    assert doc.layer == 4
    assert doc.dependencies == ["receptor_mediated_endocytosis"]
    assert doc.body.strip() == "MHC-II processing pathways are crucial for presenting antigens."

def test_parse_invalid_yaml_raises_value_error(tmp_path: Path):
    # Invalid YAML frontmatter (missing closing dashes or malformed YAML syntax)
    content = """---
concept_id: mhc_ii
layer: :invalid
dependencies:
  - receptor_mediated_endocytosis
---
MHC-II processing pathways are crucial for presenting antigens.
"""
    file_path = tmp_path / "invalid_mhc.md"
    file_path.write_text(content, encoding="utf-8")

    # Should raise ValueError
    with pytest.raises(ValueError) as exc_info:
        parse_okf_file(file_path)
    
    assert "YAML parsing error" in str(exc_info.value) or "invalid" in str(exc_info.value).lower()

def test_search_exact_match_retrieves_correct_concept(tmp_path: Path):
    from MMEE_Agent.openkb_loader import OKFIndexer
    
    # Create two different OKF files in the temp directory
    doc1_content = """---
concept_id: mhc_ii
layer: 4
dependencies: []
---
MHC-II processing pathways are key.
"""
    doc2_content = """---
concept_id: t_cell
layer: 4
dependencies: ["mhc_ii"]
---
T-cells recognize antigens presented by MHC molecules.
"""
    (tmp_path / "mhc_ii.md").write_text(doc1_content, encoding="utf-8")
    (tmp_path / "t_cell.md").write_text(doc2_content, encoding="utf-8")
    
    # Instantiate indexer and load directory
    indexer = OKFIndexer(tmp_path)
    
    # Search for "mhc_ii"
    results = indexer.search("mhc_ii")
    
    assert len(results) == 1
    assert results[0].concept_id == "mhc_ii"
    
    # Search for "t_cell"
    results_t = indexer.search("t_cell")
    assert len(results_t) == 1
    assert results_t[0].concept_id == "t_cell"

def test_search_returns_empty_on_missing_concept(tmp_path: Path):
    from MMEE_Agent.openkb_loader import OKFIndexer
    
    indexer = OKFIndexer(tmp_path)
    results = indexer.search("non_existent_concept")
    assert results == []

