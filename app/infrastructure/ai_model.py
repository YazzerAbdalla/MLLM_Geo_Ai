"""
 * Infrastructure layer for AI model interactions.
 * Provides tools for embedding text descriptions and aggregating spatial embeddings.
 """
from sentence_transformers import SentenceTransformer
import numpy as np
import pandas as pd

class Embedder:
    """
    * A class to handle text embedding using Sentence Transformers.
    """
    def __init__(self, model_name: str = 'paraphrase-multilingual-MiniLM-L12-v2'):
        """
        * Initializes the Embedder with a specific pre-trained model.
        *
        * @param {str} model_name - The name of the SentenceTransformer model to use
        """
        # Multi-lingual model for Arabic/English descriptions in CSV
        self.model = SentenceTransformer(model_name)
        
    def embed_texts(self, texts: list) -> np.ndarray:
        """
        * Generates embeddings for a list of text strings.
        *
        * @param {list} texts - A list of strings to be embedded
        * @returns {np.ndarray} An array of embeddings
        """
        return self.model.encode(texts)

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
