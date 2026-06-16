import pytest
from app.models.result import CellResult

def test_classification_result_schema_test():
    result = CellResult(
        cell_id="test_1",
        dominant_class="Residential",
        confidence=0.9,
        confidences={"residential": 0.9, "commercial": 0.05, "industrial": 0.05},
        poi_top_categories=["Food"],
        road_density=1.0,
        node_count=10,
        degree_centrality=0.1,
        clustering_coeff=0.2,
        total_road_length_m=100.0,
        graph_embedding_norm=1.0,
        text_embedding_norm=1.0,
        geometry={"type": "Polygon", "coordinates": [[[0,0], [0,1], [1,1], [1,0], [0,0]]]},
        centroid=(0.5, 0.5),
        satellite_thumbnail_url="http://example.com/thumbnail.jpg"
    )
    assert result.cell_id == "test_1"
    assert result.dominant_class == "Residential"

def test_classification_result_serialization_test():
    result = CellResult(
        cell_id="test_1",
        dominant_class="Residential",
        confidence=0.9,
        confidences={"residential": 0.9, "commercial": 0.05, "industrial": 0.05},
        geometry={"type": "Polygon", "coordinates": [[[0,0], [0,1], [1,1], [1,0], [0,0]]]},
        centroid=(0.5, 0.5)
    )
    dumped = result.model_dump()
    assert dumped["geometry"]["type"] == "Polygon"
    assert dumped["centroid"] == (0.5, 0.5)

def test_classification_result_validation_test():
    with pytest.raises(ValueError):
        CellResult(
            cell_id="test_1",
            dominant_class="Unknown", # Invalid literal
            confidence=0.9,
            confidences={"residential": 0.9, "commercial": 0.05, "industrial": 0.05},
            geometry={"type": "Polygon", "coordinates": [[[0,0], [0,1], [1,1], [1,0], [0,0]]]},
            centroid=(0.5, 0.5)
        )
