"""
 * Baseline evaluation script - POI + Random Forest.
 """
import pandas as pd
import numpy as np
import json
import os
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
from sklearn.model_selection import train_test_split
from app.infrastructure.ai_model import Embedder
from sklearn.ensemble import RandomForestClassifier
import joblib

LABEL_MAP = {"Residential": 0, "Commercial": 1, "Industrial": 2}
LABEL_INV = {v: k for k, v in LABEL_MAP.items()}

DATA_PATH = "data/raw/project.csv"
MODEL_PATH = "models/random_forest.pkl"
OUTPUT_PATH = "evals/baseline_results.json"


def main():
    if not os.path.exists(DATA_PATH):
        print(f"Error: {DATA_PATH} not found")
        return

    df = pd.read_csv(DATA_PATH)

    if "label" not in df.columns or "text_des" not in df.columns:
        print(f"Error: Required columns not found in {DATA_PATH}")
        return

    df = df.dropna(subset=["label", "text_des"])

    _, test_df = train_test_split(df, test_size=0.2, random_state=42)

    print(f"Testing on {len(test_df)} samples...")

    model = Embedder()
    embeddings = model.embed_texts(test_df["text_des"].tolist())
    
    # Convert labels to int, handling NaN
    test_df = test_df.dropna(subset=["label"])
    y_true = test_df["label"].astype(int).values

    if os.path.exists(MODEL_PATH):
        clf = joblib.load(MODEL_PATH)
    else:
        print("Training new Random Forest...")
        df = df.dropna(subset=["label"])
        all_embeddings = model.embed_texts(df["text_des"].tolist())
        y_all = df["label"].astype(int).values
        clf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
        clf.fit(all_embeddings, y_all)
        os.makedirs("models", exist_ok=True)
        joblib.dump(clf, MODEL_PATH)

    y_pred = clf.predict(embeddings)

    acc = accuracy_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred, average="macro")
    f1_per = f1_score(y_true, y_pred, average=None)
    cm = confusion_matrix(y_true, y_pred)

    results = {
        "accuracy": round(float(acc), 4),
        "f1_macro": round(float(f1), 4),
        "f1_per_class": [round(float(x), 4) for x in f1_per],
        "confusion_matrix": cm.tolist(),
    }

    os.makedirs("evals", exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Baseline accuracy: {results['accuracy']}")


if __name__ == "__main__":
    main()