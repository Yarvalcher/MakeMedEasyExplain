import re
from typing import Dict, Any

def validate_analogy(analogy: str, abstract: str) -> Dict[str, Any]:
    """Validates the educator's analogy against the raw scientific abstract.
    
    Acts as the governance gate. Checks for:
    1. Factual drift (numerical contradictions or hallucinations).
    2. Prescriptive advice (medical guidance or recommendations).
    
    Args:
        analogy: The simplified translation/analogy.
        abstract: The raw clinical text abstract.
        
    Returns:
        A dictionary containing the validation result.
    """
    analogy_lower = analogy.lower()
    abstract_lower = abstract.lower()
    
    # 1. Check for prescriptive / medical advice patterns
    prescriptive_patterns = [
        r"\byou should\b",
        r"\btake this\b",
        r"\btake these\b",
        r"\bdaily\b",
        r"\bshould take\b",
        r"\bprescribe\b",
        r"\brecommend taking\b"
    ]
    
    prescriptive_advice_detected = False
    reasoning_parts = []
    
    for pattern in prescriptive_patterns:
        match = re.search(pattern, analogy_lower)
        if match:
            prescriptive_advice_detected = True
            reasoning_parts.append(f"Prescriptive advice detected: found medical advice phrase '{match.group()}'.")
            break
            
    # 2. Check for numerical factual drift (e.g. mismatching percentages)
    analogy_percentages = re.findall(r"\b\d+%", analogy)
    abstract_percentages = re.findall(r"\b\d+%", abstract)
    
    factual_drift_detected = False
    if analogy_percentages:
        for pct in analogy_percentages:
            if pct not in abstract_percentages:
                factual_drift_detected = True
                reasoning_parts.append(f"Factual drift detected: Analogy references unverified percentage '{pct}'.")
                break

    status = "REJECTED" if (factual_drift_detected or prescriptive_advice_detected) else "APPROVED"
    reasoning = " ".join(reasoning_parts) if reasoning_parts else "Analogy is aligned with the source abstract and contains no prescriptive advice."
    
    return {
        "factual_drift_detected": factual_drift_detected,
        "prescriptive_advice_detected": prescriptive_advice_detected,
        "reasoning": reasoning,
        "status": status
    }
