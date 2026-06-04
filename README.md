# MLLM-Geo-AI Application

A web application that classifies land use in geographical areas. It analyzes maps and location data to decide if an area is Residential, Commercial, or Industrial.

**For**: Junior developers, beginners learning AI and GIS

---

## What Does This App Do?

1. **Takes a geographical area** (defined by coordinates)
2. **Collects data** about that area:
   - Points of Interest (POI) - like shops, schools, parks
   - Satellite images - aerial photos
   - Road networks - streets and highways
3. **Analyzes the data** using AI (machine learning)
4. **Produces a classification** - Residential, Commercial, or Industrial

---

## Quick Start (5 Minutes)

### Step 1: Install Requirements

```bash
# Clone and enter the project
git clone <repository-url>
cd MLLM_Geo_Ai

# Create virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate

# Install all dependencies
pip install -r requirements.txt
```

### Step 2: Download Models

The AI models (~468MB) are NOT stored in GitHub. You must download them first.

**Download from Google Drive**:
1. Go to: https://drive.google.com/file/d/1Wf3B8JpAcQXOUWi5tsIcOHXEsoQnQPuD/view?usp=sharing
2. Click the Download button (top right)
3. Extract the .zip file
4. Copy the `models/` folder to project root

**Verify Models**:
```bash
# Check files exist
ls models/sentence_transformer/
ls models/urban_mlp.pt
```

If you see file contents, the models are ready!

### Step 2b: Download Satellite Images

The satellite images are NOT stored in GitHub. You must download them separately.

**Download from Google Drive**:
1. Go to: https://drive.google.com/drive/folders/1aju_rOLVd4kmB3rDn7ppl6JMeiaL7QId?usp=sharing
2. Click the Download button (top right)
3. Extract the .zip file
4. Copy the `data/sat_images/` folder to project root (create `data/` folder if needed)

**Verify Satellite Images**:
```bash
# Check files exist
ls data/sat_images/
```

If you see image files (`.jpg`, `.png`, etc.), the satellite images are ready!

### Step 2c: Install Docker

Install docker desktop first: https://www.docker.com/products/docker-desktop/


### Step 2d: setup the environment for docker compose

```bash
copy .env.example .env
```

set the values in the .env file

```bash
set EARTH_ENGINE_PROJECT=your-earth-engine-project
set REDIS_URL=redis://localhost:6379
```
### Step 2e: Download the roads.graphml file

**Download from Google Drive**:
1. Go to: https://drive.google.com/file/d/1wFRKrYTlpA-IU29oumPZCgHDMOfIEvIg/view?usp=drive_link
2. Download the file and save it as `roads.graphml` in `data/raw/` folder

**Verify roads.graphml**:
```bash
# Check file exists
ls data/raw/roads.graphml
```

If you see the file, the roads graph is ready!


### Step 3: Run the Server

```bash
python -m app.main
```

### Step 3b: Run the Worker for cpu queue

```bash
celery -A celery_app worker -Q cpu --loglevel=info --pool=solo
```


### Step 3c: Run the Worker for gpu queue

```bash
celery -A celery_app worker -Q gpu --loglevel=info --pool=solo
```

### Step 3d: Run the redis server in side the docker 

```bash
docker compose up -d redis
```
Install docker desktop first: https://www.docker.com/products/docker-desktop/


### Step 4: Test It

Open your browser to:
```
http://localhost:8000/health
```

Expected response:
```json
{"status": "ok", "app": "MLLM-Geo-AI-App"}
```

---

## Project Structure

```
MLLM_Geo_Ai/
├── app/                    # Main application code
│   ├── config.py         # Settings (model sizes)
│   ├── main.py         # Starting point
│   ├── domain/        # Business logic (ML model)
│   ├── application/   # Use cases (classification)
│   ├── infrastructure/# External services
│   └── interfaces/    # API endpoints
├── models/              # AI models
│   ├── sentence_transformer/  # Text AI
│   └── urban_mlp.pt            # Classifier
├── scripts/            # Helper scripts
├── tests/               # Tests
├── docs/                # Documentation
├── data/                # Data files
│   └── sat_images/     # Satellite images
```

---

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.10+ | Use 3.10, 3.11, or 3.12 |
| pip | Latest | Comes with Python |
| Git | Any | For cloning |

### Optional (Recommended Later)
| Requirement | Purpose |
|-------------|---------|
| Redis | Better job tracking |
| GEE account | Real satellite data |

---

## Key Commands

| Command | Description |
|---------|-------------|
| `python -m app.main` | Start API server |
| `pytest tests/` | Run tests |
| `python scripts/download_model.py` | Download AI model |
| `python scripts/process_data.py` | Process data |

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v1/load-area` | POST | Load area (returns 501 - planned) |
| `/api/v1/classify` | POST | Classify (returns 501 - planned) |

**Note**: Some endpoints return HTTP 501 because async features are planned for future. See docs/project_status.md.

---

## Understanding the Code

### Starting Point
- `app/main.py` - This runs first

### Machine Learning
- `app/domain/mlp_model.py` - The classifier
- `app/infrastructure/ai_model.py` - Text AI (embeddings)
- `app/infrastructure/image_encoder.py` - Image AI

### APIs
- `app/interfaces/api.py` - All web endpoints

---

## Common Problems

### "Module not found"
**Fix**: Run `pip install -r requirements.txt`

### "Redis connection failed"
**Fix**: App still works but shows warning. Optional for now.

### "Model not found"
**Fix**: Run `python scripts/download_model.py`

### "Satellite images not found"
**Fix**: Download from the Drive link in the onboarding PDF and place in `data/sat_images/`

See docs/windows_setup_guide.md for Windows-specific help.

---

## Documentation

| Document | What It Covers |
|----------|--------------|
| docs/quick_start_demo.md | First run guide |
| docs/project_status.md | What's working |
| docs/file_status.md | File guide |
| docs/windows_setup_guide.md | Windows help |

---

## Dependencies

### Core (Required)
```
fastapi
geopandas
pandas
numpy
sentence-transformers
torch
torchvision
osmnx
networkx
pillow
```

### Optional
```
redis          # Job tracking
earthengine-api  # Satellite data
streamlit      # UI
```

Full list in `requirements.txt`.

---

## Architecture

This app uses Domain-Driven Design (DDD):

```
app/
├── domain/         # Business rules, ML models
├── application/  # Use cases (what the app does)
├── infrastructure/# External services (AI, databases)
└── interfaces/   # API endpoints (web)
```

---

## Testing

Run the tests:

```bash
pytest tests/ -v
```

Run specific test:

```bash
pytest tests/test_image_encoder.py -v
```

---

## Future Features

These are planned:
- Full async pipeline (Celery)
- Real satellite imagery (GEE)
- Large area processing
- Natural language query

See docs/project_status.md for details.

---

## Getting Help

1. **Start here**: docs/quick_start_demo.md
2. **Check status**: docs/project_status.md
3. **Understand files**: docs/file_status.md
4. **Windows help**: docs/windows_setup_guide.md

---

## License

This is a student project for educational purposes.

---

**Questions? Don't hesitate to ask for help! Start with the quick start guide.**