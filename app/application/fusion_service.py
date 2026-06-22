"""
 * Multi-Modal Classification Use Case.
 *
 * Orchestrates the end-to-end process of classifying urban grid cells using
 * multiple data modalities including POI text data, satellite imagery,
 * and road network graph features.
"""

import os
import json

import numpy as np
import torch
import geopandas as gpd

from app.infrastructure.job_store import job_store
from app.infrastructure.image_encoder import ImageEncoder
from app.infrastructure.road_network import RoadNetworkLoader
from app.infrastructure.ai_model import Embedder
from app.domain.mlp_model import UrbanMLP
from app.domain.spatial_service import create_multimodal_feature


class MultiModalClassificationUseCase:
    """
     * Orchestrates the encoding and classification of multi-modal features.
     *
     * This class serves as the main orchestrator for the urban land use
     * classification pipeline. It integrates three data modalities:
     *
     * - Point of Interest (POI) text descriptions
     * - Satellite imagery
     * - Road network metrics
     *
     * AI-9 / FR-29 additions:
     * - Embedding norm tracking
     * - Extra explainability metadata
     """

    def __init__(self, checkpoint_path: str = "models/urban_mlp.pt"):
        """
         * Initializes the multi-modal classification use case.
         *
         * Components:
         * - POI encoder
         * - Image encoder
         * - MLP classifier (loaded from trained checkpoint)
         *
         * Classifier runs in evaluation mode for inference.
         """
        self.poi_encoder = Embedder()
        self.image_encoder = ImageEncoder()
        self.classifier = UrbanMLP()

        if os.path.exists(checkpoint_path):
            print(f"[FUSION] Loading trained checkpoint: {checkpoint_path}")
            try:
                ckpt = torch.load(checkpoint_path, map_location="cpu")
                if isinstance(ckpt, dict) and "state_dict" in ckpt:
                    self.classifier.load_state_dict(ckpt["state_dict"])
                elif isinstance(ckpt, dict) and any(k.startswith("net.") for k in ckpt):
                    self.classifier.load_state_dict(ckpt)
                else:
                    print(f"[FUSION] WARNING: Unknown checkpoint format, using random weights")
                print(f"[FUSION] Checkpoint loaded successfully")
            except Exception as e:
                print(f"[FUSION] WARNING: Failed to load checkpoint: {e}, using random weights")
        else:
            print(f"[FUSION] WARNING: No checkpoint at {checkpoint_path}, using random weights")

        self.classifier.eval()

    def save_result(self, job_id: str, features: list[dict]) -> str:
        """
         * Saves classification results as a GeoJSON file.
         *
         * @param job_id: Unique identifier for classification job
         * @param features: Result features array
         *
         * @returns str: Path to saved GeoJSON file
         """
        os.makedirs("data/results", exist_ok=True)

        path = f"data/results/{job_id}.geojson"

        fc = {
            "type": "FeatureCollection",
            "features": features
        }

        with open(path, "w") as f:
            json.dump(fc, f)

        return path

    def execute(self, job_id: str, grid_id: str, fusion_method: str = "concat"):
        """
         * Executes the complete multi-modal classification pipeline.
         *
         * Workflow:
         * 1. Load grid data
         * 2. Extract multimodal features
         * 3. Encode images in batch
         * 4. Fuse POI + image + graph features
         * 5. Run classifier inference
         * 6. Post-process predictions
         * 7. Save results
         *
         * Progress tracking:
         * - 10%: loading_grid
         * - 30%: encoding_features
         * - 80%: running_inference
         * - 100%: completed
         *
         * @param job_id: Job tracking identifier
         * @param grid_id: Grid identifier
         """

        try:
            # ==================================================
            # Step 1: Load Grid Data
            # ==================================================

            job_store.update_job(
                job_id,
                status="running",
                step="loading_grid",
                progress=0.1
            )

            grid_data = job_store.get_grid(grid_id)

            if not grid_data:
                raise ValueError(
                    f"Grid {grid_id} not found."
                )

            grid_gdf = grid_data["gdf"]

            # ==================================================
            # Step 2: Prepare Cell Data
            # ==================================================

            job_store.update_job(
                job_id,
                step="encoding_features",
                progress=0.3
            )

            cell_data = []

            for idx, cell in grid_gdf.iterrows():

                cell_id = cell.get(
                    "cell_id",
                    idx
                )

                img_path = os.path.join(
                    "data",
                    "sat_images",
                    f"cell_{cell_id}.png"
                )

                cell_data.append({
                    "cell_id": cell_id,
                    "text": cell.get(
                        "text_des",
                        ""
                    ),
                    "img_path": img_path,
                    "node_count": cell.get(
                        "node_count",
                        0
                    ),
                    "total_length": cell.get(
                        "total_length",
                        0.0
                    ),
                    "avg_degree": cell.get(
                        "avg_degree",
                        0.0
                    ),
                    "geometry": cell.geometry,
                    "poi_categories": cell.get(
                        "poi_categories",
                        []
                    ),

                    # Explainability defaults
                     "text_embedding_norm": 0.0,
                     "graph_embedding_norm": 0.0
                })

            # ==================================================
            # Step 3: Batch Image Encoding
            # ==================================================

            img_paths = [
                c["img_path"]
                for c in cell_data
            ]

            img_embeddings = (
                self.image_encoder.encode_batch(
                    img_paths
                )
            )

            # ==================================================
            # Step 4: Feature Fusion
            # ==================================================

            features = []
            cell_ids = []

            for i, cell_info in enumerate(cell_data):

                # ----------------------------------------------
                # 1. POI Text Embedding
                # ----------------------------------------------

                text = cell_info["text"]

                # [VAL-A] Runtime text verification
                print(f"[VAL-A] CELL={i}")
                print(f"[VAL-A] TEXT_EXISTS={bool(text)}")
                text_str = str(text) if text else ""
                print(f"[VAL-A] TEXT_LENGTH={len(text_str)}")
                print(f"[VAL-A] TEXT_PREVIEW={text_str[:100]}")

                if text:
                    poi_emb = (
                        self.poi_encoder.embed_texts(
                            [text]
                        )[0]
                    )
                else:
                    poi_emb = np.zeros(
                        384,
                        dtype=np.float32
                    )

                # ----------------------------------------------
                # 2. Image Embedding
                # ----------------------------------------------

                img_emb = img_embeddings[i]

                # ----------------------------------------------
                # 3. Graph Features
                # ----------------------------------------------

                graph_feat = np.array([
                    cell_info["node_count"],
                    cell_info["total_length"],
                    cell_info["avg_degree"]
                ], dtype=np.float32)

                # ==================================================
                # AI-9 (FR-29)
                # Embedding Norm Explainability
                # ==================================================

                text_embedding_norm = float(
                    np.linalg.norm(poi_emb)
                )

                graph_embedding_norm = float(
                    np.linalg.norm(graph_feat)
                )

                cell_info[
                    "text_embedding_norm"
                ] = text_embedding_norm

                cell_info[
                    "graph_embedding_norm"
                ] = graph_embedding_norm

                # ----------------------------------------------
                # 4. Multimodal Fusion
                # ----------------------------------------------

                # [VAL-D] Fusion input verification
                poi_norm_d = float(np.linalg.norm(poi_emb))
                img_norm_d = float(np.linalg.norm(img_emb))
                graph_norm_d = float(np.linalg.norm(graph_feat))
                print(f"[VAL-D] CELL={i} POI_NORM={poi_norm_d:.4f} IMG_NORM={img_norm_d:.4f} GRAPH_NORM={graph_norm_d:.4f}")

                use_attention = (fusion_method == "attention")
                fused = create_multimodal_feature(
                    poi_emb,
                    img_emb,
                    graph_feat,
                    use_attention=use_attention
                )

                features.append(fused)

                cell_ids.append(
                    cell_info["cell_id"]
                )

            # ==================================================
            # Step 5: Model Inference
            # ==================================================

            job_store.update_job(
                job_id,
                step="running_inference",
                progress=0.8
            )

            X = torch.tensor(
                np.array(features),
                dtype=torch.float32
            )

            with torch.no_grad():
                probs = (
                    self.classifier(X)
                    .numpy()
                )

            # ==================================================
            # Step 6: Post Processing
            # ==================================================

            results = []

            classes = [
                "Residential",
                "Commercial",
                "Industrial"
            ]

            for i, cell_id in enumerate(cell_ids):

                cell_info = cell_data[i]

                p = probs[i]

                dominant_idx = int(
                    np.argmax(p)
                )

                # ----------------------------------------------
                # Road Density Calculation (DEF-014: use projected CRS)
                # ----------------------------------------------

                node_count = (
                    cell_info["node_count"]
                )

                total_length = (
                    cell_info["total_length"]
                )

                from shapely.geometry import shape
                geom = cell_info["geometry"]
                if hasattr(geom, "area"):
                    try:
                        import geopandas as gpd
                        gdf_proj = gpd.GeoDataFrame(geometry=[geom], crs="EPSG:4326")
                        gdf_proj = gdf_proj.to_crs("EPSG:3857")
                        cell_area_m2 = gdf_proj.geometry.area.iloc[0]
                    except Exception:
                        cell_area_m2 = geom.area
                else:
                    cell_area_m2 = 0.0

                cell_area_km2 = (
                    cell_area_m2 / 1e6
                    if cell_area_m2 > 0
                    else 1.0
                )

                road_density = (
                    (total_length / 1000)
                    / cell_area_km2
                    if cell_area_km2 > 0
                    else 0.0
                )

                # ----------------------------------------------
                # Top POI Categories
                # ----------------------------------------------

                poi_top = cell_info.get(
                    "poi_categories", []
                )[:3]

                # [VAL-E] Output serialization check
                print(f"[VAL-E] CELL={i} TEXT_EMBEDDING_NORM={cell_info.get('text_embedding_norm', 0.0)}")
                print(f"[VAL-E] CELL={i} POI_TOP={poi_top}")

                # ==================================================
                # Final Result Object
                # ==================================================

                geometry = cell_info["geometry"]

                geom_dict = getattr(geometry,
                                    "__geo_interface__",
                                    {"type": "Polygon",
                                     "coordinates": []})

                centroid = (
                    float(geometry.centroid.x),
                    float(geometry.centroid.y)
                ) if hasattr(geometry, "centroid") else (0.0, 0.0)

                results.append({
                    "type": "Feature",
                    "properties": {
                        "cell_id": cell_id,
                        "dominant_class": classes[dominant_idx],
                        "confidence": float(p[dominant_idx]),
                        "confidences": {
                            "residential": float(p[0]),
                            "commercial": float(p[1]),
                            "industrial": float(p[2])
                        },
                        "road_density": float(road_density),
                        "node_count": int(node_count),
                        "degree_centrality": 0.0,
                        "clustering_coeff": 0.0,
                        "total_road_length_m": float(cell_info.get("total_length", 0.0)),
                        "poi_top_categories": poi_top,
                        "text_embedding_norm": float(cell_info.get("text_embedding_norm", 0.0)),
                        "graph_embedding_norm": float(cell_info.get("graph_embedding_norm", 0.0)),
                        "centroid": centroid,
                        "satellite_thumbnail_url": f"/api/v1/thumbnails/{grid_id}/{cell_id}.jpg"
                    },
                    "geometry": geom_dict
                })

            # ==================================================
            # Step 7: Save Results
            # ==================================================

            result_path = self.save_result(
                job_id,
                results
            )

            job_store.update_job(
                job_id,
                status="completed",
                step="done",
                progress=1.0,
                result_data=results,
                result_url=(
                    "/api/v1/"
                    f"classification-result/"
                    f"{job_id}"
                )
            )

        except Exception as e:
            """
             * Handles pipeline failures.
             * Updates job status to failed.
             * Re-raises so the caller never overwrites "failed" with "completed".
             """

            job_store.update_job(
                job_id,
                status="failed",
                error=str(e)
            )
            raise