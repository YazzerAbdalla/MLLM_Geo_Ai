import networkx as nx
from shapely.geometry import Point, LineString, mapping


def _extract_graph_from_grid_data(grid_data):
    """
    Try to extract a NetworkX graph from different possible storage shapes.
    """
    if isinstance(grid_data, dict):
        for key in ("graph", "nx_graph", "road_graph", "G"):
            if key in grid_data and grid_data[key] is not None:
                return grid_data[key]

    for attr in ("graph", "nx_graph", "road_graph", "G"):
        graph = getattr(grid_data, attr, None)
        if graph is not None:
            return graph

    return None

def _graph_to_geojson(graph):
    """
    Convert a NetworkX graph into GeoJSON FeatureCollection:
    - Nodes as Point features
    - Edges as LineString features
    """
    if graph is None:
        return None

    if graph.number_of_nodes() > 1:
        degree_centrality = nx.degree_centrality(graph)
    else:
        degree_centrality = {node_id: 0.0 for node_id in graph.nodes()}

    features = []

    # Nodes -> Points
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

    # Edges -> LineStrings
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

