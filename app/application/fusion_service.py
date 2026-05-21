"""
 * Multi-Modal Classification Use Case.
 * 
 * Orchestrates the end-to-end process of classifying urban grid cells using
 * multiple data modalities including POI text data, satellite imagery, and
 * road network graph features.
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
     * 
     * This class serves as the main orchestrator for the urban land use
     * classification pipeline. It integrates three data modalities:
     * - Point of Interest (POI) text descriptions
     * - Satellite imagery
     * - Road network metrics (node count, total length, average degree)
     """
    def __init__(self):
        """
         * Initializes the multi-modal classification use case.
         * 
         * Sets up the three core components:
         * - POI encoder: Converts text descriptions to embeddings
         * - Image encoder: Processes satellite imagery into feature vectors
         * - Classifier: MLP model that predicts land use categories
         * 
         * The classifier is set to evaluation mode for inference.
         """
        self.poi_encoder = Embedder()
        self.image_encoder = ImageEncoder()
        self.classifier = UrbanMLP()
        self.classifier.eval()

    def save_result(self, job_id: str, features: list[dict]) -> str:
        """
         * Saves classification results as a GeoJSON file.
         * 
         * Creates a FeatureCollection containing all classified cells with
         * their geometry, predicted land use class, confidence scores,
         * and derived metrics.
         * 
         * @param job_id: str - Unique identifier for the classification job
         * @param features: list[dict] - Array of feature objects containing
         *                               classification results for each cell
         * @returns str - File path to the saved GeoJSON result file
         * 
         * @example
         * result_path = useCase.save_result("job_123", [
         *     {
         *         "cell_id": "cell_001",
         *         "dominant_class": "Residential",
         *         "confidences": {"Residential": 0.85, "Commercial": 0.10, "Industrial": 0.05}
         *     }
         * ])
         """
        os.makedirs("data/results", exist_ok=True)
        path = f"data/results/{job_id}.geojson"
        fc = {"type": "FeatureCollection", "features": features}
        with open(path, "w") as f:
            json.dump(fc, f)
        return path
        
    def execute(self, job_id: str, grid_id: str):
        """
         * Executes the complete classification pipeline for a specific grid.
         * 
         * This is the main entry point that orchestrates the entire workflow:
         * 1. Loads grid data and validates input
         * 2. Extracts multimodal features from each cell
         * 3. Batch encodes satellite images for efficiency
         * 4. Fuses features using spatial service
         * 5. Runs MLP classifier inference
         * 6. Post-processes results with derived metrics
         * 7. Saves results and updates job status
         * 
         * Progress is tracked through job_store at each major step:
         * - 10%: Loading grid data
         * - 30%: Encoding multimodal features
         * - 80%: Running model inference
         * - 100%: Completed
         * 
         * @param job_id: str - Unique identifier for tracking job progress
         * @param grid_id: str - Identifier for the grid to classify
         * @returns void
         * @raises ValueError - If grid is not found
         * @raises Exception - If processing fails
         * 
         * @example
         * useCase = MultiModalClassificationUseCase()
         * useCase.execute("job_456", "grid_atlanta_01")
         """
        try:
            # Step 1: Load and validate grid data (10% progress)
            """
             * Updates job status to running and progress to 10%
             * Indicates the loading grid phase has begun
             """
            job_store.update_job(job_id, status="running", step="loading_grid", progress=0.1)
            
            """
             * Retrieves grid data from job store
             * Expected structure: {'gdf': GeoDataFrame with cells}
             * Each cell should have: geometry, text_des, node_count, total_length, avg_degree
             """
            grid_data = job_store.get_grid(grid_id)
            if not grid_data:
                raise ValueError(f"Grid {grid_id} not found.")
                
            grid_gdf = grid_data['gdf']
            
            # Note: Assumptions about input data structure:
            # - POI text descriptions are attached as 'text_des' column
            # - Satellite images are stored in data/thumbnails/{grid_id}/cell_{cell_id}.png
            # - Road network features are pre-extracted or extracted on-the-fly
            
            # Step 2: Extract and prepare features (30% progress)
            """
             * Updates job progress to 30%
             * Indicates the feature encoding phase has begun
             """
            job_store.update_job(job_id, step="encoding_features", progress=0.3)
            
            """
             * Collects all cell data for batch processing
             * Extracts cell_id, text description, image path, and road network metrics
             * Preserves geometry for area calculations later
             """
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
            
            """
             * Batch encodes all satellite images at once for efficiency
             * Reduces overhead of multiple sequential API calls
             * Returns array of embeddings matching input order
             """
            img_paths = [c['img_path'] for c in cell_data]
            img_embeddings = self.image_encoder.encode_batch(img_paths)
            
            """
             * Processes each cell individually for feature fusion
             * Combines POI, image, and graph features into unified vector
             """
            features = []
            cell_ids = []
            for i, cell_info in enumerate(cell_data):
                # 1. POI Embedding: Convert text to vector representation (384-dim)
                """
                 * Encodes POI text descriptions using text embedder
                 * Empty text receives zero vector
                 * Dimension matches MiniLM model output (384)
                 """
                text = cell_info['text']
                if text:
                    poi_emb = self.poi_encoder.embed_texts([text])[0]
                else:
                    poi_emb = np.zeros(384, dtype=np.float32)
                
                # 2. Image Embedding: Use pre-computed batch encoding
                """
                 * Retrieves pre-computed image embedding from batch results
                 * Index matches original cell order
                 """
                img_emb = img_embeddings[i]
                
                # 3. Graph Features: Road network topology metrics
                """
                 * Constructs feature vector from road network metrics:
                 * - node_count: Number of intersections
                 * - total_length: Total road length in meters
                 * - avg_degree: Average connectivity of nodes
                 """
                graph_feat = np.array([
                    cell_info['node_count'],
                    cell_info['total_length'],
                    cell_info['avg_degree']
                ], dtype=np.float32)
                
                # Fuse all three modalities into single feature vector
                """
                 * Calls spatial service to concatenate all features
                 * Creates final input tensor for classifier
                 """
                fused = create_multimodal_feature(poi_emb, img_emb, graph_feat)
                features.append(fused)
                cell_ids.append(cell_info['cell_id'])
                
            # Step 3: Run classifier inference (80% progress)
            """
             * Updates job progress to 80%
             * Indicates model inference phase has begun
             """
            job_store.update_job(job_id, step="running_inference", progress=0.8)
            
            """
             * Converts numpy features to PyTorch tensor
             * Disables gradient tracking for inference efficiency
             * Returns probability distribution over three classes
             """
            X = torch.tensor(np.array(features), dtype=torch.float32)
            with torch.no_grad():
                probs = self.classifier(X).numpy()
            
            # Step 4: Post-process and format results
            """
             * Post-processes predictions into human-readable format
             * Calculates derived metrics (road density, top POIs)
             * Builds GeoJSON FeatureCollection structure
             """
            results = []
            classes = ["Residential", "Commercial", "Industrial"]
            for i, cell_id in enumerate(cell_ids):
                cell_info = cell_data[i]
                p = probs[i]
                dominant_idx = int(np.argmax(p))

                # Calculate road density (km of road per km² of area)
                """
                 * Computes road density metric:
                 * Road length (meters) -> kilometers
                 * Cell area (m²) -> km²
                 * Density = km_road / km²_area
                 """
                node_count = cell_info['node_count']
                total_length = cell_info['total_length']
                cell_area_m2 = cell_info['geometry'].area
                cell_area_km2 = cell_area_m2 / 1e6 if cell_area_m2 > 0 else 1.0
                road_density = (total_length / 1000) / cell_area_km2 if cell_area_km2 > 0 else 0.0

                # Extract top POI categories from text description
                """
                 * Parses POI text to find most frequent terms
                 * Returns top 3 categories for user display
                 * Empty text returns empty list
                 """
                text_desc = cell_info['text']
                poi_top = []
                if text_desc:
                    words = text_desc.split()
                    from collections import Counter
                    word_counts = Counter(words)
                    poi_top = [w for w, _ in word_counts.most_common(3)]
                else:
                    poi_top = []

                # Build result object with all relevant information
                """
                 * Constructs feature object with:
                 * - Predicted land use class and confidence scores
                 * - Road density metric
                 * - POI category summary
                 * - URL to satellite thumbnail
                 """
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

            # Step 5: Save results and update final status
            """
             * Saves results to GeoJSON file
             * Updates job status to completed with 100% progress
             * Provides result data and access URL for retrieval
             """
            result_path = self.save_result(job_id, results)
            job_store.update_job(
                job_id, 
                status="completed", 
                step="done", 
                progress=1.0, 
                result_data=results, 
                result_url=f"/api/v1/classification-result/{job_id}"
            )
            
        except Exception as e:
            """
             * Handles any errors during execution
             * Marks job as failed with error message
             * Ensures job store reflects failure status
             """
            job_store.update_job(job_id, status="failed", error=str(e))