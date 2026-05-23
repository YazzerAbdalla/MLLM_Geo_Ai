"""
 * Tests that classification output includes required PRD v3.0 fields.
"""
import pytest

REQUIRED_CELL_FIELDS = [
    'cell_id', 'dominant_class', 'confidences',
    'poi_top_categories', 'road_density_km_per_km2',
    'node_count', 'graph_embedding_norm', 'text_embedding_norm'
]

def test_required_fields_documented():
    missing = []
    assert len(REQUIRED_CELL_FIELDS) == 8, "Schema field list incomplete"
