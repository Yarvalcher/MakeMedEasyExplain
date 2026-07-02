from pydantic import BaseModel, Field
from google.adk.agents.llm_agent import Agent
from google.genai import types

class QueryMetadata(BaseModel):
    is_safe: bool = Field(description="False if the query involves inappropriate content, self-harm, medical diagnostic/treatment requests, or unsafe/off-topic themes.")
    safety_reason: str = Field(description="Reason for safety rejection, or empty if safe.")
    is_complex: bool = Field(description="True if the concept involves complex Layer 4/5 cellular or molecular jargon requiring analogy simplification.")
    estimated_layer: int = Field(description="Estimated layer (1-5) matching the MakeMedEasyExplain cognitive model.")
    core_concept: str = Field(description="The sanitized name of the core biological concept.")

classifier_agent = Agent(
    model='gemini-2.5-flash',
    name='classifier_agent',
    description='Evaluates input query for safety, complexity, estimated cognitive layer, and core concept.',
    generate_content_config=types.GenerateContentConfig(
        http_options=types.HttpOptions(
            retry_options=types.HttpRetryOptions(initial_delay=1.0, attempts=3)
        ),
        response_mime_type="application/json"
    ),
    instruction=(
        "Analyze the user's input query and output a structured JSON object matching the schema.\n"
        "1. Safety Check: Determine if the query is safe and appropriate (is_safe). If the query requests direct medical diagnosis, treatment recommendations, self-harm, or is off-topic/offensive, mark is_safe = False and provide a brief reason in safety_reason.\n"
        "2. Complexity: Set is_complex = True if the concept is a complex Layer 4 or 5 biological/cellular process or molecule (e.g. MHC-II processing, lymphocyte activation, DNA replication). Set is_complex = False if it is a simple Layer 1-3 concept (e.g. human teeth, hands, fingers, macro anatomy, basic stomach digestion).\n"
        "3. Estimated Layer: Estimate the cognitive layer level (1 to 5) for the query:\n"
        "   - Layer 1: Visible, lived experience (e.g. teeth, arm, pain).\n"
        "   - Layer 2: Basic mechanics (e.g. bone break, digestion).\n"
        "   - Layer 3: Macro anatomy/defenses (e.g. veins vs. arteries, white blood cells).\n"
        "   - Layer 4: Systemic processes/cellular (e.g. T-cell activation, antibodies).\n"
        "   - Layer 5: Molecular (e.g. DNA base pairs, enzyme inhibitors).\n"
        "4. Core Concept: Identify the sanitized core biological concept (e.g., 't_cell_activation', 'tooth_growth')."
    ),
    output_schema=QueryMetadata,
    output_key="query_metadata"
)
