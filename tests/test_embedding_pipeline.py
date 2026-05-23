"""
 * Tests the POI embedding pipeline.
"""
import pytest
import numpy as np
from app.infrastructure.ai_model import Embedder

def test_embedder_method_exists():
    enc = Embedder()
    assert hasattr(enc, 'embed_texts'), "embed_texts() method missing from Embedder"

def test_embedding_shape():
    enc = Embedder()
    result = enc.embed_texts(["hospital cairo", "school downtown"])
    assert result.shape == (2, 384), f"Expected (2, 384), got {result.shape}"

def test_embedding_not_zero():
    enc = Embedder()
    result = enc.embed_texts(["test"])
    assert result.sum() != 0, "Embedding is all zeros"
