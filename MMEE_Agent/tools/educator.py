import re
from typing import Dict, List

# Static lexicon mapping common biological and anatomical terms to cognitive abstraction layers (1 to 5)
LEXICON: Dict[str, int] = {
    # Layer 1: Empirical / ~99% Familiarity (Lived physical experiences)
    "arm": 1,
    "leg": 1,
    "hand": 1,
    "foot": 1,
    "head": 1,
    "skin": 1,
    "pain": 1,
    "blood": 1,
    
    # Layer 2: Functional / ~85% Familiarity (Basic bodily mechanics)
    "stomach": 2,
    "bone": 2,
    "digestion": 2,
    "infection": 2,
    "fever": 2,
    "breathing": 2,
    "heart": 2,
    "brain": 2,
    
    # Layer 3: Macro-Anatomical / ~50% Familiarity (Internal systems/general defenses)
    "cell": 3,
    "tissue": 3,
    "vein": 3,
    "artery": 3,
    "organ": 3,
    "bacteria": 3,
    "virus": 3,
    "hormone": 3,
    
    # Layer 4: Systemic Processes / ~20% Familiarity (Invisible cellular coordination)
    "antibody": 4,
    "lymphocyte": 4,
    "antigen": 4,
    "pathway": 4,
    "receptor-mediated": 4,
    "endocytosis": 4,
    "clearance": 4,
    "cytokine": 4,
    
    # Layer 5: Molecular / <5% Familiarity (Deep abstraction frontiers)
    "receptor": 5,
    "dna": 5,
    "rna": 5,
    "transcription": 5,
    "ligand": 5,
    "enzyme": 5,
    "inhibitor": 5,
    "nucleotide": 5,
    "extracellular": 5,
    "domain": 5,
}

# Pre-defined Layer 2/3 anchoring metaphors or structural blocks that make abstract terms understandable
ANCHOR_METAPHORS: List[str] = [
    "lock", "key", "door", "guard", "wall", "gate", 
    "factory", "shield", "soldier", "police", "envelope", 
    "messenger", "train", "delivery", "engine", "blueprint"
]

def identify_layer_terms(text: str) -> Dict[str, int]:
    """Analyzes input text and maps matched vocabulary to their respective cognitive layers.
    
    Args:
        text: Input explanation or scientific description.
        
    Returns:
        A dictionary mapping the matched terms to their integer abstraction layers.
    """
    detected_terms: Dict[str, int] = {}
    
    # Simple word tokenizer (lowercased, alphanumeric)
    words = re.findall(r"\b[a-zA-Z\-]+\b", text.lower())
    
    for word in words:
        if word in LEXICON:
            detected_terms[word] = LEXICON[word]
            
    return detected_terms

def check_anchoring_compliance(text: str, layer_map: Dict[str, int] = None) -> bool:
    """Checks if Layer 4/5 abstract concepts are structurally anchored using Layer 2/3 metaphors.
    
    Rule: Any text explaining a Layer 4 or Layer 5 concept must contain at least one 
    familiar Layer 2/3 structural block (metaphor/analogy word) to anchor it.
    
    Args:
        text: The simplified text to evaluate.
        layer_map: Optional pre-computed map of matched terms to cognitive layers.
        
    Returns:
        True if all Layer 4/5 terms are anchored, False otherwise.
    """
    text_lower = text.lower()
    if layer_map is None:
        layer_map = identify_layer_terms(text)
    
    # Check if there are any Layer 4 or Layer 5 terms present
    high_complexity_terms = [term for term, layer in layer_map.items() if layer >= 4]
    if not high_complexity_terms:
        # Compliant because there are no complex terms requiring anchoring
        return True
        
    # Check if the explanation utilizes anchoring metaphors
    has_anchor = any(anchor in text_lower for anchor in ANCHOR_METAPHORS)
    
    # Additional check: If it contains other unanchored complex terms explaining it 
    # without metaphor, reject it (e.g., ligand, domain, extracellular)
    if "ligand" in text_lower or "domain" in text_lower or "extracellular" in text_lower:
        if not has_anchor:
            return False
            
    return has_anchor
