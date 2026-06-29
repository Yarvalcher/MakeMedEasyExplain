import pytest
from MMEE_Agent.tools.educator import identify_layer_terms, check_anchoring_compliance

def test_identify_layer_terms():
    text = "An antibody binds to the cell receptor to prevent infection."
    
    # We expect key terms to be classified into their respective layers:
    # "antibody" -> Layer 4 (Systemic Processes)
    # "cell" -> Layer 3 (Macro-Anatomical) or Layer 4
    # "receptor" -> Layer 5 (Molecular)
    layer_map = identify_layer_terms(text)
    
    assert "antibody" in layer_map
    assert layer_map["antibody"] == 4
    
    assert "cell" in layer_map
    assert layer_map["cell"] == 3
    
    assert "receptor" in layer_map
    assert layer_map["receptor"] == 5

def test_concept_anchoring_rule_compliance():
    # Compliant text: Layer 5 term "receptor" is anchored using a Layer 2 concept "lock and key"
    compliant_text = "The receptor acts like a lock on a door, which only opens with a specific key."
    assert check_anchoring_compliance(compliant_text, {"receptor": 5}) is True
    
    # Non-compliant text: Explaining a Layer 5 term "receptor" using another unanchored Layer 5/4 term "ligand binding domain" or similar
    non_compliant_text = "The receptor is activated when a specific ligand binds to its extracellular domain."
    # The term "receptor" is not anchored using Layer 2/3 blocks, it's explained with more complex molecular concepts
    assert check_anchoring_compliance(non_compliant_text, {"receptor": 5}) is False
