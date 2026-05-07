# Multilingual Large Language Model (MLLM) and Geospatial AI for Urban Land-Use Classification

**Faculty of Engineering, Department of Urban Planning & AI**  
**Author:** *Engineering Faculty Documentation*

---

## 1. Abstract
This research project introduces an integrated framework for urban land-use classification by synthesizing Geospatial Information Systems (GIS) with state-of-the-art Multilingual Large Language Model (MLLM) embeddings. The primary objective is to automate the categorization of urban zones into Residential, Commercial, and Industrial sectors based on the semantic richness of Point-of-Interest (POI) data.

## 2. Methodology & System Architecture

### 2.1 Domain-Driven Design (DDD)
The system is architected using the **Domain-Driven Design (DDD)** paradigm, ensuring a separation of concerns that facilitates modularity and scientific scalability:
- **Domain Layer**: Encapsulates the core spatial logic, including grid generation and geometric intersections.
- **Infrastructure Layer**: Manages data persistence (CSV loading) and AI model instantiation (`paraphrase-multilingual-MiniLM-L12-v2`).
- **Application Layer**: Orchestrates the data flow (Pipeline) to derive classification results from raw inputs.

### 2.2 Spatial Reference Systems (SRS)
To maintain metric accuracy for the **500m Grid Analysis**, the system performs a transformation from WGS84 (Geographic) to **EPSG:32636 (WGS 84 / UTM zone 36N)**. This ensures that all Euclidean distance calculations and area-based joins are performed in metric units rather than degrees, which is critical for urban density analysis.

## 3. The "Cell Story" Pipeline

### 3.1 Feature Extraction via MLLM
The core innovation lies in the transformation of textual descriptions into high-dimensional semantic vectors. We utilize the **`paraphrase-multilingual-MiniLM-L12-v2`** transformer model. This model enables the system to:
1.  **Semantic Contextualization**: Understand the latent meaning behind Arabic and English POI descriptions.
2.  **Vector Embedding**: Map textual data into a 384-dimensional vector space where similar urban functions (e.g., "Hospital" and "Clinic") are positioned in close proximity.

### 3.2 Spatial Aggregation
The system employs a **Spatial Join (Intersection)** algorithm to cluster POIs within discrete 500m x 500m grid cells. For each cell, the system computes a "Cell Story" by aggregating the embeddings of all POIs within that boundary, effectively creating a "semantic fingerprint" of the neighborhood.

### 3.3 Multi-Modal Feature Vector
The UrbanMLP classifier accepts a 643-dimensional input vector:

| Component | Encoder | Dim |
|-----------|---------|-----|
| POI semantic text | paraphrase-multilingual-MiniLM-L12-v2 | 384 |
| Satellite image patch | ResNet-18 (replaced FC) | 256 |
| Road graph features | OSMnx (node_count, road_length_m, avg_degree) | 3 |
| **Total** | | **643** |

Each component is L2-normalized before concatenation.

## 4. Classification & Inference
The inference engine computes a categorical distribution over three primary land-use classes:
- **Residential**: Predicated on the presence of social infrastructure (Health, Education).
- **Commercial**: Identified through retail density and service-oriented amenities.
- **Industrial**: Detected via artisanal and manufacturing POI clusters.

The final output is a probability vector $P = [p_r, p_c, p_i]$ representing the likelihood of each land-use type for every grid cell, providing a more nuanced understanding than binary classification.

## 5. Scientific Tools & Environment
- **Deep Learning Core**: PyTorch-based Sentence-Transformers.
- **Geospatial Processing**: GeoPandas (Vectorized spatial operations).
- **Computational Geometry**: Shapely (Planar geometry objects).
- **Statistical Analysis**: NumPy & Pandas.

## 6. Conclusion
The MLLM-Geo-AI framework demonstrates that combining spatial proximity with semantic depth allows for a robust understanding of urban dynamics. Future research will focus on fine-tuning the transformer model on local urban taxonomies to increase the precision of the land-use probability distributions.
