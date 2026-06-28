import os
from typing import Dict, Any
from google.genai import Client
from google.adk.agents.llm_agent import Agent
from MMEE_Agent.validator import validate_analogy

# Define the Educator sub-agent instructions
EDUCATOR_INSTRUCTIONS = """
You are the Simplification Educator Agent for MakeMedEasyExplain.
Your task is to take a high-jargon scientific/medical abstract and translate it into a simple, visual metaphor or analogy appropriate for the general public.

You MUST follow the Concept Anchoring rule:
- Identify terms belonging to Layer 4 (Systemic Processes) or Layer 5 (Molecular).
- You are forbidden from explaining Layer 4/5 concepts using other Layer 4/5 terms.
- You must anchor your explanation using familiar Layer 2 (Functional) or Layer 3 (Macro-Anatomical) structural blocks (e.g. lock and key, gates, soldiers, shields, factories, blueprints, engines, post offices).
- Incorporate any feedback provided if this is a revision request.
- Keep the final output short, engaging, and clear.
"""

def generate_analogy(abstract: str, feedback: str = "") -> str:
    """Wraps LLM generation logic using Google ADK to generate a simplified medical analogy.
    
    Args:
        abstract: The raw medical paper abstract.
        feedback: Feedback from the validator if the previous attempt was rejected.
        
    Returns:
        The generated metaphor/analogy explanation.
    """
    # Fetch parameters from the environment setup
    project = os.environ.get("GOOGLE_CLOUD_PROJECT", "599321056091")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
    
    # Initialize the LLM agent using ADK
    educator_agent = Agent(
        model="gemini-2.5-flash",
        name="simplification_educator",
        description="Translates clinical jargon into simple Layer 2/3 analogies.",
        instruction=EDUCATOR_INSTRUCTIONS,
    )
    
    prompt = f"Abstract to simplify:\n{abstract}\n"
    if feedback:
        prompt += f"\nPrevious attempt was rejected with this feedback:\n{feedback}\nPlease revise the explanation to correct these issues."
        
    # Run the agent invocation
    response = educator_agent.run(prompt)
    return str(response).strip()

def run_orchestration_loop(abstract: str, max_retries: int = 3) -> Dict[str, Any]:
    """Coordinates Supervisor routing between the Educator and Validator agents.
    
    Supervisor Orchestration Loop:
    1. Triggers Educator to generate an analogy from the abstract.
    2. Routes the analogy to the Validator.
    3. If approved, returns the analogy.
    4. If rejected, loops back to Educator with the feedback, up to max_retries times.
    
    Args:
        abstract: The raw clinical text.
        max_retries: Max feedback loop attempts.
        
    Returns:
        A dictionary with the final validation status, analogy, and reasoning details.
    """
    feedback = ""
    attempts = 0
    last_validation_result = {}
    
    while attempts <= max_retries:
        # Step 1: Educator generates simplified analogy
        analogy = generate_analogy(abstract, feedback=feedback)
        
        # Step 2: Validator runs safety and correctness audits
        validation_result = validate_analogy(analogy, abstract)
        last_validation_result = validation_result
        
        # Step 3: Check routing decision
        if validation_result["status"] == "APPROVED":
            return {
                "status": "APPROVED",
                "analogy": analogy,
                "reasoning": validation_result["reasoning"],
                "attempts": attempts + 1
            }
            
        # Step 4: Prepare loop feedback for next attempt
        feedback = validation_result["reasoning"]
        attempts += 1
        
    # If the loop ends without approval, return the last rejected attempt
    return {
        "status": "REJECTED",
        "analogy": analogy,
        "reasoning": last_validation_result.get("reasoning", "Failed to validate within maximum retries."),
        "attempts": attempts
    }
