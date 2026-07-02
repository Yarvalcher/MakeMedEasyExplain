import pytest
from MMEE_Agent.sub_agents.classifier.agent import QueryMetadata
# We can test the schema and basic classification logic.
def test_query_metadata_schema():
    metadata = QueryMetadata(
        is_safe=True,
        safety_reason="",
        is_complex=True,
        estimated_layer=4,
        core_concept="T-Cell"
    )
    assert metadata.is_safe is True
    assert metadata.is_complex is True
    assert metadata.estimated_layer == 4
    assert metadata.core_concept == "T-Cell"
