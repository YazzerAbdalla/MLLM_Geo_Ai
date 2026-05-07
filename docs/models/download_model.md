# Model Download Guide

This guide explains how to download the AI models needed for the MLLM-Geo-AI application.

**Why?**: The models are too large (~468MB) to store in GitHub.

---

## Download Link

**[Google Drive: MLLM_Geo_Ai Models](https://drive.google.com/file/d/1Wf3B8JpAcQXOUWi5tsIcOHXEsoQnQPuD/view?usp=sharing)**

---

## Files Included

| File | Size | Description |
|------|------|-------------|
| `sentence_transformer/` | ~420 MB | Text embedding model (paraphrase-multilingual-MiniLM-L12-v2) |
| `urban_mlp.pt` | ~650 KB | Trained urban classifier |
| `random_forest.pkl` | ~48 KB | Baseline model |

**Total**: ~468 MB

---

## Download Steps

### Step 1: Download the ZIP

1. Open the Google Drive link
2. Click the **Download** button (top right of the page)
3. The file `models.zip` will download to your computer

### Step 2: Extract the ZIP

1. Locate the downloaded `models.zip` file
2. Right-click → **Extract All** (or use 7-Zip, WinRAR, etc.)
3. Extract to a convenient location

### Step 3: Copy to Project

1. Open your MLLM_Geo_Ai project folder
2. Copy the extracted `models/` folder
3. Paste it in the project root

**Expected final structure**:
```
MLLM_Geo_Ai/
├── models/
│   ├── sentence_transformer/
│   │   ├── config.json
│   │   ├── model.safetensors
│   │   └── ...
│   ├── urban_mlp.pt
│   └── random_forest.pkl
├── app/
├── scripts/
└── ...
```

---

## Verify Installation

Run these commands to verify models are installed correctly:

```bash
# Check sentence_transformer files
ls models/sentence_transformer/

# Check urban_mlp.pt
ls models/urban_mlp.pt

# Test Python loading
python -c "from sentence_transformers import SentenceTransformer; print('SentenceTransformer OK')"
python -c "import torch; m = torch.load('models/urban_mlp.pt'); print('UrbanMLP OK')"
```

If you see "OK" output, the models are ready!

---

## Troubleshooting

### "models/ folder not found"

Make sure you copied the `models/` folder (not just the contents) to the project root.

### "model.safetensors not found"

The full `models/sentence_transformer/` folder is needed, not just individual files.

### Drive says "Download quota exceeded"

Wait a few minutes or try again later. Or ask the team for an alternative copy.

---

## Need Help?

1. Check docs/project_status.md for system status
2. Ask the team on Discord/email
3. Open an issue on GitHub

---

**Last Updated**: May 2026