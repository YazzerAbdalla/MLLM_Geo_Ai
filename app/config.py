"""
 * Application Configuration.
 * Contains system-wide constants for dimensions and other settings.
"""
import os

# Model Dimensions
POI_DIM = 384     # Sentence-Transformer output dimension
IMG_DIM = 256     # ResNet18 output dimension
GRAPH_DIM = 3     # OSMnx features (node count, length, degree)
FUSION_DIM = POI_DIM + IMG_DIM + GRAPH_DIM  # 643

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
