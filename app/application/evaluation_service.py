import os
import json
import io
import tempfile
from pathlib import Path

import pandas as pd
import geopandas as gpd
from fastapi import HTTPException, UploadFile
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix

from app.infrastructure.job_store import job_store



GROUND_TRUTH_LABEL_CANDIDATES = [
    "label", "class", "land_use", "landuse", "true_label",
    "ground_truth", "gt_label", "category"
]

PRED_LABEL_CANDIDATES = [
    "dominant_class", "predicted_label", "prediction", "pred_label", "class",
    "label", "land_use", "landuse", "category"
]

MERGE_KEY_CANDIDATES = [
    "cell_id", "grid_cell_id", "feature_id", "id"
]


def _detect_column(columns, candidates):
    for col in candidates:
        if col in columns:
            return col
    return None


async def _load_table_from_upload(upload: UploadFile):
    content = await upload.read()
    suffix = Path(upload.filename or "").suffix.lower()

    if suffix == ".csv":
        return pd.read_csv(io.BytesIO(content))

    if suffix in {".geojson", ".json"}:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix or ".geojson") as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            return gpd.read_file(tmp_path)
        finally:
            try:
                os.remove(tmp_path)
            except OSError:
                pass

    raise HTTPException(status_code=400, detail="Ground truth file must be CSV or GeoJSON.")


def _result_data_to_frame(raw):
    if raw is None:
        return None

    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            return pd.DataFrame()

    if isinstance(raw, pd.DataFrame):
        return raw.copy()

    if isinstance(raw, list):
        if raw and isinstance(raw[0], dict) and raw[0].get("type") == "Feature":
            return gpd.GeoDataFrame.from_features(raw)
        return pd.DataFrame(raw)

    if isinstance(raw, dict):
        if raw.get("type") == "FeatureCollection" and "features" in raw:
            return gpd.GeoDataFrame.from_features(raw["features"])

        if "features" in raw and isinstance(raw["features"], list):
            features = raw["features"]
            if features and isinstance(features[0], dict) and features[0].get("type") == "Feature":
                return gpd.GeoDataFrame.from_features(features)

        return pd.DataFrame([raw])

    return pd.DataFrame(raw)


def _load_job_predictions(job_id: str):
    job = job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    status = str(job.get("status", "")).lower()
    if status not in {"completed", "success", "finished"}:
        raise HTTPException(status_code=409, detail="Job must be completed before evaluation.")

    raw = job.get("result_data")
    frame = _result_data_to_frame(raw)
    if frame is not None and len(frame) > 0:
        return job, frame

    for path in (
        f"data/results/{job_id}.geojson",
        f"data/results/{job_id}.csv"
    ):
        if os.path.exists(path):
            if path.endswith(".geojson"):
                return job, gpd.read_file(path)
            return job, pd.read_csv(path)

    raise HTTPException(status_code=404, detail="Prediction result not found for this job.")


def _merge_truth_and_predictions(gt_df, pred_df):
    gt = gt_df.copy()
    pred = pred_df.copy()

    gt_label_col = _detect_column(gt.columns, GROUND_TRUTH_LABEL_CANDIDATES)
    pred_label_col = _detect_column(pred.columns, PRED_LABEL_CANDIDATES)

    if not gt_label_col:
        raise HTTPException(
            status_code=400,
            detail=f"Could not detect ground truth label column. Tried: {GROUND_TRUTH_LABEL_CANDIDATES}"
        )

    if not pred_label_col:
        raise HTTPException(
            status_code=400,
            detail=f"Could not detect prediction label column. Tried: {PRED_LABEL_CANDIDATES}"
        )

    gt["_gt_label"] = gt[gt_label_col]
    pred["_pred_label"] = pred[pred_label_col]

    gt_key = _detect_column(gt.columns, MERGE_KEY_CANDIDATES)
    pred_key = _detect_column(pred.columns, MERGE_KEY_CANDIDATES)

    if gt_key and pred_key:
        merged = gt[[gt_key, "_gt_label"]].merge(
            pred[[pred_key, "_pred_label"]],
            left_on=gt_key,
            right_on=pred_key,
            how="inner"
        )
    elif "geometry" in gt.columns and "geometry" in pred.columns:
        gt["_merge_key"] = gt["geometry"].apply(lambda g: g.wkt if hasattr(g, "wkt") else None)
        pred["_merge_key"] = pred["geometry"].apply(lambda g: g.wkt if hasattr(g, "wkt") else None)

        merged = gt[["_merge_key", "_gt_label"]].merge(
            pred[["_merge_key", "_pred_label"]],
            on="_merge_key",
            how="inner"
        )
    else:
        raise HTTPException(
            status_code=400,
            detail="No common spatial key found (cell_id/id) and no geometry column available."
        )

    merged = merged.dropna(subset=["_gt_label", "_pred_label"])

    if merged.empty:
        raise HTTPException(
            status_code=400,
            detail="No matching rows found between ground truth and predictions."
        )

    return merged


async def evaluate_job(job_id: str, ground_truth_file: UploadFile):
    gt_df = await _load_table_from_upload(ground_truth_file)
    _, pred_df = _load_job_predictions(job_id)
    merged = _merge_truth_and_predictions(gt_df, pred_df)

    y_true = merged["_gt_label"].astype(str).tolist()
    y_pred = merged["_pred_label"].astype(str).tolist()

    labels = sorted(set(y_true) | set(y_pred))

    overall_accuracy = float(accuracy_score(y_true, y_pred))
    macro_f1 = float(f1_score(y_true, y_pred, average="macro", labels=labels, zero_division=0))
    weighted_f1 = float(f1_score(y_true, y_pred, average="weighted", labels=labels, zero_division=0))
    per_class_scores = f1_score(y_true, y_pred, average=None, labels=labels, zero_division=0)
    cm = confusion_matrix(y_true, y_pred, labels=labels)

    evaluation_result = {
        "job_id": job_id,
        "num_samples": len(merged),
        "labels": labels,
        "overall_accuracy": overall_accuracy,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "spatial_accuracy": overall_accuracy,
        "per_class_f1": {
            label: float(score)
            for label, score in zip(labels, per_class_scores)
        },
        "confusion_matrix": cm.tolist()
    }

    try:
        job_store.update_job(job_id, evaluation=evaluation_result)
    except Exception:
        pass

    return evaluation_result

##

def export_evaluation_csv(job_id: str):
    job = job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    evaluation = job.get("evaluation")
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation result not found for this job")

    df = pd.json_normalize(evaluation, sep="_")

    for col in df.columns:
        if df[col].apply(lambda x: isinstance(x, (list, dict))).any():
            df[col] = df[col].apply(lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, (list, dict)) else x)

    return df.to_csv(index=False).encode("utf-8")