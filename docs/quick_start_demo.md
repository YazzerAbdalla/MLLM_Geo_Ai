# Quick Start Demo Guide

This guide helps you run the MLLM-Geo-AI application for the first time.

**Goal**: Run a successful classification with mock data  
**Time**: About 15-30 minutes  
**For**: Junior developers, beginners

---

## Step 1: Check Python

Open your terminal (command prompt) and run:

```bash
python --version
```

**Expected Output**:
```
Python 3.10.x
```

or newer (3.11, 3.12, etc.)

If you get "python is not recognized", you need to install Python first.

---

## Step 2: Create Virtual Environment

Create a new virtual environment (recommended):

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# OR (alternative Windows)
python -m venv venv
venv\Scripts\activate
```

**Expected**: Your terminal shows `(.venv)` or `(venv)` at the start of the line.

---

## Step 3: Install Dependencies

Install all required packages:

```bash
pip install -r requirements.txt
```

**Expected**: Many lines of installation output ending with "Successfully installed..."

**Time**: This may take several minutes (especially PyTorch).

---

## Step 4: Verify Model Files

Check that the model is downloaded:

```bash
ls models/sentence_transformer/
```

**Expected Output** (at least):
```
config.json
model.safetensors
tokenizer.json
```

If you see errors, download the model:

```bash
python scripts/download_model.py
```

---

## Step 5: Start the API Server

Run this command:

```bash
python -m app.main
```

**Expected Output**:
```
INFO:     Application startup complete
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Or similar with warnings (that's okay for now).

**Keep this terminal open!** Don't close it.

---

## Step 6: Test Health Check

Open a new terminal window and run:

```bash
curl http://localhost:8000/health
```

**Expected Output**:
```json
{"status":"ok","app":"MLLM-Geo-AI-App"}
```

**Alternative**: Open this URL in your browser:
```
http://localhost:8000/health
```

---

## Step 7: First Classification (Mock Mode)

Now let's run a classification. We'll use empty "modalities" to skip real downloads:

```bash
curl -X POST http://localhost:8000/api/v1/load-area \
  -H "Content-Type: application/json" \
  -d '{"bbox": [31.1, 30.0, 31.15, 30.05], "grid_size": 1000, "modalities": []}'
```

**Expected Output**:
```json
{
  "error": "Async task pipeline not yet implemented",
  "message": "This feature is planned for future implementation",
  "docs": "See docs/project_status.md for system status",
  "workaround": "Use a smaller synchronous workflow or wait for future release"
}
```

**What This Means**:
This endpoint requires the async task system which is not yet implemented. This is expected!

The demo functionality is **limited** because the full async pipeline is a future feature. For now, we can:

1. Run the tests (`pytest tests/`), which work differently
2. Explore the existing code
3. Wait for future implementation

---

## Alternative: Run the Tests

The test suite uses synchronous test clients and works without async tasks:

```bash
pytest tests/ -v
```

**Expected**: Tests will run, some may pass, some may fail (due to Redis).

---

## Understanding What's Working

After quick start, here's what's working:

| Feature | Status |
|---------|--------|
| API server starts | WORKS |
| Health check | WORKS |
| ML encoders loaded | WORKS |
| PyTorch models | WORKS |
| /load-area endpoint | WORKS (returns 501 - planned) |
| /classify endpoint | WORKS (returns 501 - planned) |

---

## What to Do Next

### If You Want to Learn More

1. **Read the code**: Look at `app/` folder structure
2. **Run tests**: `pytest tests/test_image_encoder.py`
3. **Understand models**: Read `app/domain/mlp_model.py`

### For More Complex Workflows

1. **Install Redis**: See docs/windows_setup_guide.md
2. **Set up GEE**: Advanced feature (not required)
3. **Learn ML pipeline**: Read `app/application/fusion_service.py`

---

## Common Problems

### Problem: "ModuleNotFoundError"

**Cause**: Dependencies not installed

**Solution**:
```bash
pip install -r requirements.txt
```

### Problem: "No module named 'app'"

**Cause**: Not in the right directory

**Solution**: Make sure you're in the MLLM_Geo_Ai folder:
```bash
cd D:\Projects\MLLM_Geo_Ai
```

### Problem: "Port 8000 is in use"

**Cause**: Another program is using port 8000

**Solution**: 
1. Close other programs
2. Or change port in `app/main.py` (advanced)

---

## File Locations

After setup, your project looks like this:

```
MLLM_Geo_Ai/
├── app/                    # Main application code
│   ├── config.py         # Settings
│   ├── main.py          # Entry point
│   ├── domain/         # Business logic
│   ├── application/    # Use cases
│   ├── infrastructure/# External services
│   └── interfaces/    # API endpoints
├── models/              # ML models
│   ├── sentence_transformer/
│   └── urban_mlp.pt
├── scripts/            # Helper scripts
├── tests/              # Tests
├── docs/               # Documentation
└── data/              # Data (generated)
```

---

## Summary

In this quick start, you:

1. [x] Checked Python version
2. [x] Created virtual environment
3. [x] Installed dependencies  
4. [x] Verified model files
5. [x] Started API server
6. [x] Tested health endpoint
7. [x] Tried classification (learned about future features)

**Congratulations!** You successfully ran the MLLM-Geo-AI application.

---

## Next Steps

- Read docs/project_status.md for full system status
- Look at docs/file_status.md to understand files
- Explore the `app/` code to learn the architecture

**Don't worry** if some things don't work yet - the async features are planned for future release!