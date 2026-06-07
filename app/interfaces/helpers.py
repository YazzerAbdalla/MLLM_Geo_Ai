import os, json
import networkx as nx
import osmnx as ox
from shapely.geometry import Point, LineString, mapping
from pathlib import Path
from fastapi import HTTPException, UploadFile, status

def _extract_graph_from_grid_data(grid_data, max_nodes=500, simplify=True):
    """
    Load the cached road graph from roads.graphml and clip it to the grid bbox.
    """
    if not isinstance(grid_data, dict):
        return None

    bbox = grid_data.get("bbox")
    if not bbox:
        return None

    graphml_path = "data/raw/roads.graphml"
    if not os.path.exists(graphml_path):
        return None

    G = ox.load_graphml(graphml_path)

    # bbox format in your project: [min_x, min_y, max_x, max_y]
    min_x, min_y, max_x, max_y = bbox

    # keep only nodes inside bbox
    nodes_in_bbox = []
    for node_id, data in G.nodes(data=True):
        x = data.get("x")
        y = data.get("y")
        if x is None or y is None:
            continue
        if min_x <= x <= max_x and min_y <= y <= max_y:
            nodes_in_bbox.append(node_id)

    if not nodes_in_bbox:
        return None

    G = G.subgraph(nodes_in_bbox).copy()

    if simplify:
        G = _simplify_graph_for_response(G, max_nodes=max_nodes)
    else:
        if G.number_of_nodes() > max_nodes:
            G = _limit_graph_nodes(G, max_nodes=max_nodes)

    return G


def _simplify_graph_for_response(graph, max_nodes=500):
    if graph is None:
        return None

    if graph.number_of_nodes() <= max_nodes:
        return graph

    try:
        undirected = graph.to_undirected()
        largest_cc = max(nx.connected_components(undirected), key=len)
        graph = graph.subgraph(largest_cc).copy()
    except Exception:
        graph = graph.copy()

    if graph.number_of_nodes() <= max_nodes:
        return graph

    return _limit_graph_nodes(graph, max_nodes=max_nodes)


def _limit_graph_nodes(graph, max_nodes=500):
    if graph is None:
        return None

    if graph.number_of_nodes() <= max_nodes:
        return graph

    top_nodes = sorted(
        graph.nodes(),
        key=lambda n: graph.degree(n),
        reverse=True
    )[:max_nodes]

    return graph.subgraph(top_nodes).copy()


def _graph_to_geojson(graph):
    if graph is None:
        return None

    if graph.number_of_nodes() > 1:
        degree_centrality = nx.degree_centrality(graph)
    else:
        degree_centrality = {node_id: 0.0 for node_id in graph.nodes()}

    features = []

    for node_id, data in graph.nodes(data=True):
        x = data.get("x")
        y = data.get("y")
        if x is None or y is None:
            continue

        features.append({
            "type": "Feature",
            "id": f"node-{node_id}",
            "geometry": mapping(Point(x, y)),
            "properties": {
                "element_type": "node",
                "node_id": str(node_id),
                "degree": int(graph.degree(node_id)),
                "centrality": float(degree_centrality.get(node_id, 0.0)),
            }
        })

    if graph.is_multigraph():
        edge_iter = graph.edges(keys=True, data=True)
        for u, v, key, data in edge_iter:
            edge_id = data.get("edge_id", f"{u}-{v}-{key}")
            geom = data.get("geometry")

            if geom is None:
                u_data = graph.nodes[u]
                v_data = graph.nodes[v]
                ux, uy = u_data.get("x"), u_data.get("y")
                vx, vy = v_data.get("x"), v_data.get("y")
                if None in (ux, uy, vx, vy):
                    continue
                geom = LineString([(ux, uy), (vx, vy)])

            features.append({
                "type": "Feature",
                "id": f"edge-{edge_id}",
                "geometry": mapping(geom),
                "properties": {
                    "element_type": "edge",
                    "edge_id": str(edge_id),
                    "u": str(u),
                    "v": str(v),
                    "length_m": float(data.get("length_m", data.get("length", 0.0)) or 0.0),
                    "highway": data.get("highway"),
                }
            })
    else:
        for idx, (u, v, data) in enumerate(graph.edges(data=True)):
            edge_id = data.get("edge_id", f"{u}-{v}-{idx}")
            geom = data.get("geometry")

            if geom is None:
                u_data = graph.nodes[u]
                v_data = graph.nodes[v]
                ux, uy = u_data.get("x"), u_data.get("y")
                vx, vy = v_data.get("x"), v_data.get("y")
                if None in (ux, uy, vx, vy):
                    continue
                geom = LineString([(ux, uy), (vx, vy)])

            features.append({
                "type": "Feature",
                "id": f"edge-{edge_id}",
                "geometry": mapping(geom),
                "properties": {
                    "element_type": "edge",
                    "edge_id": str(edge_id),
                    "u": str(u),
                    "v": str(v),
                    "length_m": float(data.get("length_m", data.get("length", 0.0)) or 0.0),
                    "highway": data.get("highway"),
                }
            })

    return {
        "type": "FeatureCollection",
        "features": features
    }

# helper for End Point -3 POST /api/v1/evaluate

MAX_GROUND_TRUTH_SIZE = 10 * 1024 * 1024  # 10 MB

ALLOWED_EXTENSIONS = {".json", ".geojson"}
ALLOWED_CONTENT_TYPES = {
    "application/json",
    "application/geo+json",
    "application/octet-stream",
}


async def validate_ground_truth_file(file: UploadFile) -> None:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ground_truth_file is required."
        )

    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only .json or .geojson files are allowed."
        )

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported content type: {file.content_type}"
        )

    content = await file.read(MAX_GROUND_TRUTH_SIZE + 1)

    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty."
        )

    if len(content) > MAX_GROUND_TRUTH_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="ground_truth_file exceeds the maximum allowed size of 10 MB."
        )

    try:
        data = json.loads(content.decode("utf-8"))
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be UTF-8 encoded JSON/GeoJSON."
        )
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON/GeoJSON file."
        )

    if not isinstance(data, dict) or data.get("type") != "FeatureCollection":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ground_truth_file must be a GeoJSON FeatureCollection."
        )

    if "features" not in data or not isinstance(data["features"], list):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GeoJSON must contain a valid 'features' array."
        )

    await file.seek(0)