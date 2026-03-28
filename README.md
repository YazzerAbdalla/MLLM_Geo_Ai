# MLLM-Geo-AI Application

## Overview

A high-performance spatial classification system designed to analyze point-of-interest (POI) data and classify land-use types (Residential, Commercial, Industrial) through a combination of Geospatial analysis and Multilingual Large Language Model (MLLM) embeddings.

### Architecture
- **Domain-Driven Design (DDD)**: Clean separation between Domain, Application, and Infrastructure layers.
- **TDD (Test-Driven Development)**: Built with automated spatial verification.

### Core Tools & Frameworks
- **Web Interface**: FastAPI (Asynchronous Python)
- **Spatial Engine**: GeoPandas, Shapely (EPSG:32636 projection)
- **AI Core**: Sentence-Transformers (PyTorch)
- **Data Handling**: Pandas, NumPy
- **Testing**: PyTest

### Model Name
- **`paraphrase-multilingual-MiniLM-L12-v2`**: A specialized multilingual transformer model used to create "Cell Stories" by embedding textual descriptions of urban points.

---

## Getting Started

### Prerequisites:
- Python 3.10+
- `pip` and `venv`

### Installation:
1.  **Clone the Repository**:
    ```bash
    git clone <repository-url>
    cd MLLM_Geo_Ai
    ```
2.  **Activate Virtual Environment**:
    ```bash
    # Windows
    .\.venv\Scripts\activate
    ```
3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

### Running the App:
```bash
python -m app.main
```
The server will start at `http://localhost:8000`.

---

## Detailed Documentation
For a deep dive into the scientific methodology, spatial theory, and classification logic, please refer to the academic paper:
- [Scientific Analysis & Methodology](./docs/Scientific_Analysis.md)

---

## API Usage

### Classify Data:
`POST /api/v1/classify`
- **Description**: Triggers the MLLM-Geo-AI pipeline on the `project.csv` dataset.
- **Response**:
    ```json
    {
      "status": "success",
      "data": [
        {
          "cell_id": 0,
          "residential": 0.85,
          "commercial": 0.10,
          "industrial": 0.05,
          "dominant_class": "Residential"
        }
      ]
    }
    ```
