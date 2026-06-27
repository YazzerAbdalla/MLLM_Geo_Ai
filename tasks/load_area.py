"""
 * Celery load_area task.
"""
import os
import osmnx as ox
from app.infrastructure.road_network import RoadNetworkLoader
from celery_app import celery_app
from dotenv import load_dotenv

load_dotenv()


@celery_app.task(bind=True)
def load_area_task(self, job_id: str, bbox: list, grid_size: int, modalities: list = None):
    import ee
    from app.infrastructure.job_store import JobStore
    from celery.exceptions import Ignore

    # Initialize GEE in this worker process
    project_id = os.getenv('EARTH_ENGINE_PROJECT')
    if project_id:
        try:
            ee.Initialize(project=project_id)
        except Exception as e:
            print(f'GEE init warning: {e}')

    store = JobStore()
    if modalities is None:
        modalities = ["poi", "image", "graph"]

    try:
        job = store.get_job(job_id) or {}

        if job.get("status") == "cancelled":
           raise Ignore()
        
        store.update_job(job_id, status="running", step="generating_grid", progress=0.1)

        from app.domain.spatial_service import generate_grid
        min_x, min_y, max_x, max_y = bbox
        grid_gdf = generate_grid((min_x, min_y, max_x, max_y), cell_size_m=grid_size)

        job = store.get_job(job_id) or {}

        if job.get("status") == "cancelled":
           raise Ignore()

        grid_id = f"grid_{job_id[:8]}"

        store.update_job(job_id, step="downloading_satellite", progress=0.3)
        if "image" in modalities:
            from app.infrastructure.satellite_loader import SatelliteImageLoader
            loader = SatelliteImageLoader()
            loader.download_for_grid(grid_gdf, grid_id)

        job = store.get_job(job_id) or {}

        if job.get("status") == "cancelled":
           raise Ignore()


        store.update_job(job_id, step="downloading_road_network", progress=0.6)
        if "graph" in modalities:
           store.update_job(job_id, step="downloading_road_network", progress=0.6)

           graphml_path = "data/raw/roads.graphml"
       
           # bbox عندك: (min_x, min_y, max_x, max_y)
           # RoadNetworkLoader عايزها: (north, south, east, west)
           road_bbox = (max_y, min_y, max_x, min_x)
       
           # 1) Load من الكاش لو الملف موجود
           if os.path.exists(graphml_path):
               G = ox.load_graphml(graphml_path)
           else:
               # 2) Load من OSM لو الملف مش موجود
               loader = RoadNetworkLoader(bbox=road_bbox)
               G = loader.load()
       
               os.makedirs("data/raw", exist_ok=True)
               ox.save_graphml(G, graphml_path)
       
           # 3) جهز loader للـ features
           graph_loader = RoadNetworkLoader()
           graph_loader.G = G
           graph_loader.nodes_gdf, graph_loader.edges_gdf = ox.graph_to_gdfs(G)
       
           # 4) احسب graph features لكل cell
           node_counts = []
           total_lengths = []
           avg_degrees = []
       
           for _, row in grid_gdf.iterrows():
               feats = graph_loader.get_graph_features_for_geometry(row.geometry)
               node_counts.append(float(feats[0]))
               total_lengths.append(float(feats[1]))
               avg_degrees.append(float(feats[2]))
       
           grid_gdf["node_count"] = node_counts
           grid_gdf["total_length"] = total_lengths
           grid_gdf["avg_degree"] = avg_degrees

           #فحص الإلغاء بعد تحميل الشبكة
           job = store.get_job(job_id) or {}

           if job.get("status") == "cancelled":
               raise Ignore()

        store.update_job(job_id, step="processing_poi", progress=0.8)
        if "poi" in modalities:
            from app.infrastructure.data_loader import load_project_data
            from app.domain.spatial_service import join_points_to_grid

            csv_path = "data/raw/project.csv"
            points_gdf = load_project_data(csv_path)

            joined = join_points_to_grid(points_gdf, grid_gdf)

            if len(joined) > 0:
                poi_counts = joined.groupby("cell_id").size()
                grid_gdf["poi_count"] = (
                    grid_gdf["cell_id"].map(poi_counts).fillna(0).astype(int)
                )
                text_des = joined.groupby("cell_id")["text_des"].apply(
                    lambda x: " ".join(x.dropna().astype(str))
                )
                grid_gdf["text_des"] = (
                    grid_gdf["cell_id"].map(text_des).fillna("")
                )

                poi_categories = joined.groupby("cell_id")["category"].apply(
                    lambda x: list(dict.fromkeys(x.dropna().astype(str)))  # unique, preserve order
                )
                grid_gdf["poi_categories"] = (
                    grid_gdf["cell_id"].map(poi_categories).fillna("").apply(
                        lambda v: v if isinstance(v, list) else []
                    )
                )

                os.makedirs("data/raw", exist_ok=True)
                pois_path = f"data/raw/pois_{grid_id}.geojson"
                pois_gdf = joined.drop(columns=["index_right"], errors="ignore")
                pois_gdf["amenity"] = pois_gdf.get("category", "Unknown")
                pois_gdf.to_file(pois_path, driver="GeoJSON")
            else:
                grid_gdf["poi_count"] = 0
                grid_gdf["text_des"] = ""

            job = store.get_job(job_id) or {}
            if job.get("status") == "cancelled":
                raise Ignore()

        store.store_grid(grid_id, {"gdf": grid_gdf, "bbox": bbox})
       
        store.update_job(job_id, status="completed", step="done", progress=1.0, grid_id=grid_id, num_cells=len(grid_gdf))

    except Ignore:
        store.update_job(job_id, status="cancelled", step="cancelled")
        return    
    except Exception as e:
        store.update_job(job_id, status="failed", error=str(e))
        raise