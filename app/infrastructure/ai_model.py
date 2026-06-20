"""
 * Infrastructure layer for AI model interactions.
 * Provides tools for embedding text descriptions and aggregating spatial embeddings.
 """
import pickle
from sentence_transformers import SentenceTransformer
import numpy as np
import pandas as pd
import redis
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


class Embedder:
    """
    * A class to handle text embedding using Sentence Transformers.
    """
    def __init__(self, model_name: str = 'paraphrase-multilingual-MiniLM-L12-v2'):
        """
         * Initializes the Embedder with a specific pre-trained model.
        """
        import traceback
        print("[VAL-B] Loading SentenceTransformer...")
        try:
            self.model = SentenceTransformer(model_name)
            print(f"[VAL-B] Model loaded: {model_name}")
        except Exception as e:
            print(f"[VAL-B] CRASHED: {type(e).__name__}: {e}")
            traceback.print_exc()
            raise

        try:
            self.redis_client = redis.from_url(REDIS_URL, decode_responses=False)
            self.redis_client.ping()
        except Exception:
            self.redis_client = None

    def encode_with_cache(self, text: str, grid_id: str, cell_idx: int) -> np.ndarray:
        """
         * Encode text with Redis cache-aside pattern.
        """
        if not self.redis_client:
            return self.model.encode(text)

        cache_key = f"emb:poi:{grid_id}:{cell_idx}"
        cached = self.redis_client.get(cache_key)
        if cached:
            return pickle.loads(cached)

        embedding = self.model.encode(text)
        self.redis_client.set(cache_key, pickle.dumps(embedding))
        return embedding
        
    def embed_texts(self, texts: list) -> np.ndarray:
        """
        * Generates embeddings for a list of text strings.
        *
        * @param {list} texts - A list of strings to be embedded
        * @returns {np.ndarray} An array of embeddings
        """
        print(f"[VAL-C] Received {len(texts)} text(s)")
        result = self.model.encode(texts)
        for i, t in enumerate(texts):
            emb = result[i] if result.ndim > 1 else result
            norm = float(np.linalg.norm(emb))
            print(f"[VAL-C] CELL={i} SHAPE={emb.shape} DTYPE={emb.dtype} NORM={norm:.4f}")
            if norm < 0.001:
                print(f"[VAL-C] *** ZERO EMBEDDING DETECTED *** text_preview={str(t)[:80]}")
        return result

def aggregate_cell_embeddings(joined_gdf: pd.DataFrame) -> pd.DataFrame:
    """
    * Groups by cell_id and aggregates embeddings by calculating the mean.
    *
    * @param {pd.DataFrame} joined_gdf - GeoDataFrame containing 'cell_id' and 'embedding' columns
    * @returns {pd.DataFrame} A DataFrame with aggregated embeddings per cell
    """
    # Assuming joined_gdf has 'cell_id' and 'embedding'
    # Each embedding is an array.
    cell_embeddings = joined_gdf.groupby('cell_id')['embedding'].apply(lambda x: np.mean(np.stack(x), axis=0))
    return cell_embeddings.reset_index()
