إذا كنت تريد اختبار **MLLM-Geo-AI بالكامل End-to-End يدويًا باستخدام Postman** قبل المناقشة، فأنصحك بالترتيب التالي. هذا يغطي كل الـ User Journey من اختيار المنطقة حتى التقييم والتصدير.

---

# 0. Startup Verification

تأكد أولاً أن كل الخدمات تعمل:

```bash
redis-cli ping
```

يجب أن ترجع:

```text
PONG
```

ثم:

```bash
celery -A app.celery_app inspect active
```

وتأكد أن الـ worker ظاهر.

---

# 1. Health Check

### Request

```http
GET /health
```

### Expected

```json
{
  "status": "ok"
}
```

### Verify

* FastAPI يعمل
* Redis متصل
* Database متاحة

---

# 2. Load Area

### Request

```http
POST /api/v1/load-area
```

Body

```json
{
  "bbox": [31.20, 30.00, 31.21, 30.01],
  "grid_size": 1000,
  "modalities": ["poi"]
}
```

### Expected

```json
{
  "job_id": "...",
  "status": "queued"
}
```

احفظ:

```text
job_id
```

---

# 3. Poll Area Status

### Request

```http
GET /api/v1/area-status/{job_id}
```

كرر كل 2 ثانية.

### Expected Flow

```text
queued
↓
running
↓
completed
```

### Save

عند completion:

```json
{
  "grid_id": "grid_xxx",
  "num_cells": 4
}
```

احفظ:

```text
grid_id
```

---

# 4. Grid Preview

### Request

```http
GET /api/v1/grid/{grid_id}/preview
```

### Verify

* 200 OK
* GeoJSON FeatureCollection
* يوجد Cells

---

# 5. Grid Details

### Request

```http
GET /api/v1/grid/{grid_id}/details
```

### Verify

```json
{
  "cell_count": 4
}
```

---

# 6. POI Endpoint

### Request

```http
GET /api/v1/grid/{grid_id}/pois
```

### Verify

* POIs موجودة
* Categories صحيحة

---

# 7. Graph Topology

### Request

```http
GET /api/v1/grid/{grid_id}/graph-topology
```

### Verify

* لا يوجد Timeout
* GeoJSON يرجع

إذا فشل هنا:

```text
Known issue from audit report
```

---

# 8. Classification

### Request

```http
POST /api/v1/classify
```

Body

```json
{
  "grid_id": "grid_xxx",
  "modalities": ["poi"],
  "fusion_method": "concat"
}
```

### Expected

```json
{
  "job_id": "...",
  "status": "queued"
}
```

احفظ:

```text
classification_job_id
```

---

# 9. Poll Classification Status

### Request

```http
GET /api/v1/classify-status/{classification_job_id}
```

كرر كل 2 ثانية.

### Expected

```text
queued
↓
running
↓
completed
```

إذا بقي:

```text
running
```

أكثر من دقيقة:

افحص:

```bash
celery inspect active
```

و

```bash
celery inspect reserved
```

---

# 10. Classification Result

### Request

```http
GET /api/v1/classification-result/{classification_job_id}
```

### Verify Schema

لكل Cell:

```json
{
  "cell_id": 1,
  "dominant_class": "Residential",
  "confidence": 0.93,
  "road_density": 0.1,
  "node_count": 5,
  "geometry": {},
  "centroid": [],
  "poi_top_categories": []
}
```

---

# 11. Validate Output

تحقق من:

```text
confidence between 0 and 1
```

```text
dominant_class not null
```

```text
geometry exists
```

```text
road_density >= 0
```

---

# 12. Export GeoJSON

### Request

```http
GET /api/v1/export/{classification_job_id}?format=geojson
```

### Verify

* File downloaded
* Valid GeoJSON

---

# 13. Export CSV

### Request

```http
GET /api/v1/export/{classification_job_id}?format=csv
```

### Verify

* CSV downloaded
* Rows count matches cells count

---

# 14. Export Shapefile

### Request

```http
GET /api/v1/export/{classification_job_id}?format=shapefile
```

### Verify

* ZIP downloaded
* Contains:

```text
.shp
.dbf
.shx
```

---

# 15. Evaluation

Upload Ground Truth CSV.

Example:

```csv
cell_id,true_class
1,Residential
2,Commercial
3,Industrial
4,Residential
```

### Request

```http
POST /api/v1/evaluate
```

Form Data:

```text
job_id = classification_job_id
ground_truth = file.csv
```

### Verify

Returns:

```json
{
  "evaluation_id": "..."
}
```

---

# 16. Evaluation Export

### Request

```http
GET /api/v1/evaluate/{evaluation_id}/export
```

### Verify

CSV downloaded.

---

# 17. Training Validation

### Request

```http
POST /api/v1/mllm/train
```

Test invalid dataset:

```json
{
  "dataset_path": "fake.csv"
}
```

Expected:

```http
400
```

---

# 18. Delete Job

### Request

```http
DELETE /api/v1/jobs/{job_id}
```

### Verify

```json
{
  "status": "cancelled"
}
```

---

# Final E2E Success Criteria

المشروع يعتبر ناجح End-to-End إذا نجحت السلسلة التالية كاملة:

```text
Health
   ↓
Load Area
   ↓
Area Status
   ↓
Grid Preview
   ↓
Grid Details
   ↓
POIs
   ↓
Classify
   ↓
Classification Status
   ↓
Classification Result
   ↓
Export GeoJSON
   ↓
Export CSV
   ↓
Evaluate
   ↓
Evaluation Export
```

إذا وصلت إلى **Evaluation Export بنجاح** فأنت أثبت عمليًا أن الـ backend الأساسي يعمل من البداية للنهاية، وهو أقوى دليل يمكنك عرضه في المناقشة.
