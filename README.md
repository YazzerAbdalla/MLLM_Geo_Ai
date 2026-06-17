# MLLM-Geo-AI Application

A web application that classifies land use in geographical areas. It analyzes maps and location data to determine whether an area is **Residential**, **Commercial**, or **Industrial**.

**Target Audience:** Junior developers, beginners learning AI and GIS

---

# What Does This App Do?

The application:

1. Takes a geographical area defined by coordinates.
2. Collects multiple data sources:

   * Points of Interest (POIs)
   * Satellite imagery
   * Road networks
3. Processes and analyzes the data using machine learning models.
4. Produces a land-use classification:

   * Residential
   * Commercial
   * Industrial

---

# Project Structure

```text
MLLM_Geo_Ai/
├── app/
│   ├── config.py
│   ├── main.py
│   ├── domain/
│   ├── application/
│   ├── infrastructure/
│   └── interfaces/
├── models/
│   ├── sentence_transformer/
│   └── urban_mlp.pt
├── scripts/
├── tests/
├── docs/
├── data/
│   ├── sat_images/
│   └── raw/
└── requirements.txt
```

---

# Prerequisites

## Required

| Requirement | Version | Notes                  |
| ----------- | ------- | ---------------------- |
| Python      | 3.10+   | Recommended: 3.10–3.12 |
| pip         | Latest  | Included with Python   |
| Git         | Any     | Repository management  |

## Optional

| Requirement         | Purpose                |
| ------------------- | ---------------------- |
| Docker Desktop      | Redis container        |
| Redis               | Job queue backend      |
| Google Earth Engine | Real satellite imagery |

---

# Required Downloads

The following assets are not stored in GitHub and must be downloaded separately.

---

## 1. AI Models

### Download

Google Drive:

```text
https://drive.google.com/file/d/1Wf3B8JpAcQXOUWi5tsIcOHXEsoQnQPuD/view?usp=sharing
```

### Installation

Extract the archive and copy the contents to:

```text
models/
├── sentence_transformer/
└── urban_mlp.pt
```

### Verify

```bash
ls models/sentence_transformer/
ls models/urban_mlp.pt
```

---

## 2. Satellite Images

### Download

Google Drive:

```text
https://drive.google.com/drive/folders/1aju_rOLVd4kmB3rDn7ppl6JMeiaL7QId?usp=sharing
```

### Installation

Extract and place files under:

```text
data/
└── sat_images/
```

### Verify

```bash
ls data/sat_images/
```

---

## 3. Road Network Graph

### Download

Google Drive:

```text
https://drive.google.com/file/d/1wFRKrYTlpA-IU29oumPZCgHDMOfIEvIg/view?usp=drive_link
```

### Installation

Place the file at:

```text
data/raw/roads.graphml
```

### Verify

```bash
ls data/raw/roads.graphml
```

---

# Environment Setup

## 1. Clone Repository

```bash
git clone <repository-url>
cd MLLM_Geo_Ai
```

---

## 2. Create Virtual Environment

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

### Linux / macOS

```bash
python -m venv .venv
source .venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Configure Environment Variables

Create the environment file:

```bash
copy .env.example .env
```

Edit `.env`:

```env
EARTH_ENGINE_PROJECT=your-earth-engine-project
REDIS_URL=redis://localhost:6379
```

---

# Infrastructure Setup

## Install Docker Desktop

Download and install Docker Desktop:

```text
https://www.docker.com/products/docker-desktop/
```

---

## Start Redis

```bash
docker compose up -d redis
```

Verify:

```bash
docker ps
```

You should see a running Redis container.

---

# Running the Application

## Start the API Server

```bash
python -m app.main
```

---

## Start Celery Worker (Single Worker)

```bash
celery -A celery_app worker --loglevel=info --pool=solo -Q cpu,gpu 
```

---

## OR Start Dedicated Workers

### CPU Queue

```bash
celery -A celery_app worker \
  -Q cpu \
  --loglevel=info \
  --pool=solo
```

### GPU Queue

```bash
celery -A celery_app worker \
  -Q gpu \
  --loglevel=info \
  --pool=solo
```

---

# Verify Installation

Open:

```text
http://localhost:8000/health
```

Expected response:

```json
{
  "status": "ok",
  "app": "MLLM-Geo-AI-App"
}
```

---

# API Endpoints

| Endpoint            | Method | Description                       |
| ------------------- | ------ | --------------------------------- |
| `/health`           | GET    | Health check                      |
| `/api/v1/load-area` | POST   | Load area (planned)               |
| `/api/v1/classify`  | POST   | Classification endpoint (planned) |

> Some endpoints currently return **HTTP 501 Not Implemented** because the asynchronous pipeline is still under development.

---

# Key Commands

| Command                            | Description      |
| ---------------------------------- | ---------------- |
| `python -m app.main`               | Start API server |
| `pytest tests/`                    | Run all tests    |
| `python scripts/download_model.py` | Download models  |
| `python scripts/process_data.py`   | Process datasets |

---

# Understanding the Code

## Application Entry Point

```text
app/main.py
```

Starts the FastAPI application.

---

## Machine Learning Components

| File                                  | Purpose                  |
| ------------------------------------- | ------------------------ |
| `app/domain/mlp_model.py`             | Land-use classifier      |
| `app/infrastructure/ai_model.py`      | Text embeddings          |
| `app/infrastructure/image_encoder.py` | Satellite image encoding |

---

## API Layer

```text
app/interfaces/api.py
```

Contains all REST endpoints.

---

# Testing

Run all tests:

```bash
pytest tests/ -v
```

Run a specific test:

```bash
pytest tests/test_image_encoder.py -v
```

---

# Common Problems

## Module Not Found

**Error**

```text
ModuleNotFoundError
```

**Fix**

```bash
pip install -r requirements.txt
```

---

## Redis Connection Failed

The application can still run without Redis but background jobs may not work.

Ensure Redis is running:

```bash
docker compose up -d redis
```

---

## Model Not Found

Verify:

```bash
ls models/
```

Make sure all required model files are downloaded and placed correctly.

---

## Satellite Images Not Found

Verify:

```bash
ls data/sat_images/
```

Ensure images were downloaded and extracted to the correct directory.

---

# Documentation

| Document                      | Description              |
| ----------------------------- | ------------------------ |
| `docs/quick_start_demo.md`    | Quick demo guide         |
| `docs/project_status.md`      | Current project status   |
| `docs/file_status.md`         | File-by-file explanation |
| `docs/windows_setup_guide.md` | Windows-specific setup   |

---

# Architecture

The application follows Domain-Driven Design (DDD).

```text
app/
├── domain/          # Business rules and ML logic
├── application/     # Use cases
├── infrastructure/  # External services and integrations
└── interfaces/      # API layer
```

---

# Future Features

Planned improvements:

* Full Celery-based async processing pipeline
* Google Earth Engine integration
* Large-area classification workflows
* Natural language geographic queries
* Enhanced dashboard and visualization tools

---

# License

This is a student project intended for educational purposes.

---

# Getting Help

1. Read `docs/quick_start_demo.md`
2. Check `docs/project_status.md`
3. Review `docs/file_status.md`
4. Consult `docs/windows_setup_guide.md`

Questions and contributions are welcome.
