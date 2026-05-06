# Windows Setup Guide

This guide helps you set up MLLM-Geo-AI on Windows.

**For**: Windows users, beginners  
**Last Updated**: May 2026

---

## Common Windows Issues

Windows can be tricky with Python GIS packages. This page helps you solve common problems.

---

## Issue 1: Python Not Found

### Symptom
```
'python' is not recognized as an internal or external command
```

### Solution

1. **Option A**: Add Python to PATH
   - Open Windows Settings → Search "Edit environment variables"
   - Find "Path" in System variables
   - Add: `C:\Users\YourName\AppData\Local\Programs\Python\Python312`
   - Add: `C:\Users\YourName\AppData\Local\Programs\Python\Python312\Scripts`

2. **Option B**: Use full path
   ```bash
   C:\Users\YourName\AppData\Local\Programs\Python\Python312\python.exe --version
   ```

---

## Issue 2: pip Not Installing Packages

### Symptom
```
ERROR: Could not find a version that satisfies the requirement
```

### Solution

1. Update pip first:
   ```bash
   python -m pip install --upgrade pip
   ```

2. Use specific versions if needed:
   ```bash
   pip install numpy pandas --only-binary :all:
   ```

---

## Issue 3: GDAL / rasterio Errors

### Symptom
```
ImportError: No module named 'gdal'
```
or
```
rasterio/_gdal.cp312-win_amd64.pyd not found
```

### Cause
GDAL is tricky on Windows. It needs precompiled binaries.

### Solution

**Option A**: Use wheel files (recommended)

1. Get the correct wheel from:
   https://www.lfd.uci.edu/~gohlke/pythonlibs/

2. Install the wheel:
   ```bash
   pip install Gdal-3.8.4-cp312-cp312-win_amd64.whl
   ```

**Option B**: Use conda (easier for GIS)

1. Install Miniconda:
   https://docs.conda.io/en/latest/miniconda.html

2. Create environment:
   ```bash
   conda create -n geo python=3.10
   conda activate geo
   conda install gdal rasterio geopandas
   ```

**Option C**: Skip GDAL for now
- The app can run with mock data without GDAL
- Focus on learning the ML parts first

---

## Issue 4: OSMnx Installation Fails

### Symptom
```
ERROR: OSMnx dependency rtree failed
```

### Solution

**Option A**: Install rtree separately
```bash
pip install rtree
```

**Option B**: Use conda
```bash
conda install -c conda-forge osmnx
```

---

## Issue 5: Redis on Windows

### Symptom
```
redis-server is not recognized
```

### Solutions

**Option A**: Use Memurai (recommended for Windows)
1. Download from: https://www.memurai.com/
2. Install and run: `memurai`
3. It works like Redis but is native Windows

**Option B**: Use Windows Subsystem for Linux (WSL)
1. Enable WSL in Windows Features
2. Install Ubuntu from Microsoft Store
3. Run Redis in WSL: `sudo apt install redis-server`

**Option C**: Skip Redis (not required for basics)
- App shows warning but works
- Async jobs won't track but other features work

---

## Issue 6: Long Path Issues

### Symptom
```
The system cannot find the path specified
```

### Solution

1. Enable long paths in Windows:
   ```bash
   reg add "HKLM\SYSTEM\CurrentControlSet\Control\FileSystem" /v LongPathsEnabled /t REG_DWORD /d 1
   ```

2. Or use shorter folder names

---

## Issue 7: Port 8000 Already in Use

### Symptom
```
ERROR: [Errno 10048] Only one usage of each socket address
```

### Solutions

**Option A**: Find and kill the process
```bash
netstat -ano | findstr :8000
taskkill /PID <number> /F
```

**Option B**: Use a different port
Edit `app/main.py`:
```python
uvicorn.run("app.main:app", host="0.0.0.0", port=8001)
```

---

## Issue 8: Virtual Environment Problems

### Symptom
```
无法将项识别为 cmdlet
```
("Cannot recognize the item")

### Solution (Windows PowerShell)

1. Enable scripts:
   ```bash
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

2. Or use cmd.exe instead of PowerShell

---

## Issue 9: Antivirus Blocking Downloads

### Symptom
- Downloads fail or are very slow
- Files get deleted

### Solution

1. Temporarily disable Windows Defender
2. Or add Python to exclusions:
   - Windows Security → Virus & threat protection
   - Manage settings → Exclusion

---

## Recommended Windows Setup

### Step 1: Install Python
- Download from: https://www.python.org/downloads/
- Check "Add to PATH"
- Use Python 3.10 or 3.11

### Step 2: Create Project Folder
```bash
cd D:\Projects
mkdir MLLM_Geo_Ai
cd MLLM_Geo_Ai
```

### Step 3: Create Virtual Environment
```bash
python -m venv .venv
.venv\Scripts\activate
```

### Step 4: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 5: Test It
```bash
python -m app.main
```
Open http://localhost:8000/health in browser

---

## Alternative: Use Anaconda

If you have problems with pip, try Anaconda:

1. **Download**: https://www.anaconda.com/download
2. **Create environment**:
   ```bash
   conda create -n geo python=3.10
   conda activate geo
   ```
3. **Install packages**:
   ```bash
   conda install geopandas pandas numpy scikit-learn
   pip install sentence-transformers torch torchvision
   conda install -c conda-forge osmnx
   ```

---

## Need More Help?

1. See docs/quick_start_demo.md for first steps
2. See docs/project_status.md for what's working
3. Search error messages online
4. Ask on discussion forums

---

## Summary

| Problem | Quick Fix |
|---------|----------|
| Python not found | Add to PATH or use full path |
| Package install fails | Use conda or wheels |
| GDAL/rasterio | Use conda or skip |
| Redis | Use Memurai or skip |
| Port in use | Change port or kill process |
| Scripts not working | Use cmd.exe not PowerShell |

**Don't give up!** Windows setup is the hardest part. Once running, the app works well.