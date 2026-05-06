"""
 * Multi-Modal Classification Use Case.
 """
import numpy as np
import torch
import geopandas as gpd
import json
from app.infrastructure.job_store import job_store
from app.infrastructure.image_encoder import ImageEncoder
from app.infrastructure.road_network import RoadNetworkLoader
from app.infrastructure.ai_model import Embedder
from app.domain.mlp_model import UrbanMLP
from app.domain.spatial_service import create_multimodal_feature
import os


class MultiModalClassificationUseCase:
    """
     * Orchestrates the encoding and classification of multi-modal features.
    """
    def __init__(self):
        self.poi_encoder = Embedder()
        self.image_encoder = ImageEncoder()
        self.classifier = UrbanMLP()
        self.classifier.eval()

    def save_result(self, job_id: str, features: list[dict]) -> str:
        os.makedirs("data/results", exist_ok=True)
        path = f"data/results/{job_id}.geojson"
        fc = {"type": "FeatureCollection", "features": features}
        with open(path, "w") as f:
            json.dump(fc, f)
        return path
        
    def execute(self, job_id: str, grid_id: str):
        """
         * Execute classification for a specific grid.
         * Updates progress in job_store.
         """
        try:
            job_store.update_job(job_id, status="running", step="loading_grid", progress=0.1)
            
            grid_data = job_store.get_grid(grid_id)
            if not grid_data:
                raise ValueError(f"Grid {grid_id} not found.")
                
            grid_gdf = grid_data['gdf']
            
            # Here we assume POIs are already attached to grid_gdf (as 'text_des')
            # and images are in data/thumbnails/{grid_id}/cell_{cell_id}.png
            # For road networks, we assume the graph features are pre-extracted
            # or we extract them here. For this MVP, let's extract them here if not present.
            
            job_store.update_job(job_id, step="encoding_features", progress=0.3)
            
            # Collect all image paths first for batch encoding
            cell_data = []
            for idx, cell in grid_gdf.iterrows():
                cell_id = cell.get('cell_id', idx)
                img_path = os.path.join("data", "sat_images", f"cell_{cell_id}.png")
                text = cell.get('text_des', '')
                node_count = cell.get('node_count', 0)
                total_length = cell.get('total_length', 0.0)
                avg_degree = cell.get('avg_degree', 0.0)
                cell_data.append({
                    'cell_id': cell_id,
                    'text': text,
                    'img_path': img_path,
                    'node_count': node_count,
                    'total_length': total_length,
                    'avg_degree': avg_degree,
                    'geometry': cell.geometry
                })
            
            # Batch encode all images at once
            img_paths = [c['img_path'] for c in cell_data]
            img_embeddings = self.image_encoder.encode_batch(img_paths)
            
            # Process each cell
            features = []
            cell_ids = []
            for i, cell_info in enumerate(cell_data):
                # 1. POI Embedding
                text = cell_info['text']
                if text:
                    poi_emb = self.poi_encoder.embed_texts([text])[0]
                else:
                    poi_emb = np.zeros(384, dtype=np.float32)
                
                # 2. Image Embedding (from batch)
                img_emb = img_embeddings[i]
                
                # 3. Graph Features
                graph_feat = np.array([
                    cell_info['node_count'], 
                    cell_info['total_length'], 
                    cell_info['avg_degree']
                ], dtype=np.float32)
                
                fused = create_multimodal_feature(poi_emb, img_emb, graph_feat)
                features.append(fused)
                cell_ids.append(cell_info['cell_id'])
                
            job_store.update_job(job_id, step="running_inference", progress=0.8)
            
            X = torch.tensor(np.array(features), dtype=torch.float32)
            with torch.no_grad():
                probs = self.classifier(X).numpy()
            
            results = []
            classes = ["Residential", "Commercial", "Industrial"]
            for i, cell_id in enumerate(cell_ids):
                cell_info = cell_data[i]
                p = probs[i]
                dominant_idx = int(np.argmax(p))

                node_count = cell_info['node_count']
                total_length = cell_info['total_length']
                cell_area_m2 = cell_info['geometry'].area
                cell_area_km2 = cell_area_m2 / 1e6 if cell_area_m2 > 0 else 1.0
                road_density = (total_length / 1000) / cell_area_km2 if cell_area_km2 > 0 else 0.0

                text_desc = cell_info['text']
                poi_top = []
                if text_desc:
                    words = text_desc.split()
                    from collections import Counter
                    word_counts = Counter(words)
                    poi_top = [w for w, _ in word_counts.most_common(3)]
                else:
                    poi_top = []

                results.append({
                    "cell_id": cell_id,
                    "dominant_class": classes[dominant_idx],
                    "confidences": {
                        "Residential": float(p[0]),
                        "Commercial": float(p[1]),
                        "Industrial": float(p[2])
                    },
                    "road_density_km_per_km2": float(road_density),
                    "node_count": int(node_count),
                    "poi_top_categories": poi_top,
                    "satellite_thumbnail_url": f"/api/v1/thumbnails/{{grid_id}}/{cell_id}.jpg".replace("{grid_id}", grid_id)
                })

            result_path = self.save_result(job_id, results)
            job_store.update_job(job_id, status="completed", step="done", progress=1.0, result_data=results, result_url=f"/api/v1/classification-result/{job_id}")
            
        except Exception as e:
            job_store.update_job(job_id, status="failed", error=str(e))
