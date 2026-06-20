"""Generate confusion matrix on held-out test set"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, classification_report, accuracy_score, f1_score, precision_score, recall_score
import torch
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.domain.mlp_model import UrbanMLP
from app.config import FUSION_DIM, POI_DIM, IMG_DIM, GRAPH_DIM
from app.infrastructure.ai_model import Embedder

df = pd.read_csv("data/raw/project.csv")
print(f"Total samples: {len(df)}")

# 3-way stratified split: 70% train, 15% val, 15% test
train_df, temp_df = train_test_split(df, test_size=0.30, random_state=42, stratify=df["label"])
val_df, test_df = train_test_split(temp_df, test_size=0.50, random_state=42, stratify=temp_df["label"])

train_idxs = set(train_df.index); val_idxs = set(val_df.index); test_idxs = set(test_df.index)
print(f"Train: {len(train_df)}  Val: {len(val_df)}  Test: {len(test_df)}")
print(f"Sum:  {len(train_df) + len(val_df) + len(test_df)}")
print(f"Overlaps — train-val: {len(train_idxs & val_idxs)}  train-test: {len(train_idxs & test_idxs)}  val-test: {len(val_idxs & test_idxs)}")
print()

for name, split in [("Train", train_df), ("Val", val_df), ("Test", test_df)]:
    print(f"{name}:")
    print(split["label"].value_counts().sort_index().to_string())
    print()

# Encode features
print("Encoding...")
poi_enc = Embedder()

def encode(df):
    X, y = [], []
    for _, row in df.iterrows():
        text = str(row["text_des"]) if pd.notna(row.get("text_des")) else ""
        poi_emb = poi_enc.embed_texts([text])[0] if text else np.zeros(POI_DIM, dtype=np.float32)
        img_emb = np.zeros(IMG_DIM, dtype=np.float32)
        graph_feat = np.array([0, 0, 0], dtype=np.float32)
        X.append(np.concatenate([poi_emb, img_emb, graph_feat]).astype(np.float32))
        y.append(int(row["label"]))
    return np.array(X), np.array(y, dtype=np.int64)

X_train, y_train = encode(train_df)
X_val, y_val = encode(val_df)
X_test, y_test = encode(test_df)
print(f"X: train {X_train.shape}  val {X_val.shape}  test {X_test.shape}")

# Load checkpoint
ckpt_raw = torch.load("models/urban_mlp.pt", map_location="cpu", weights_only=True)
sd = ckpt_raw["state_dict"] if isinstance(ckpt_raw, dict) and "state_dict" in ckpt_raw else ckpt_raw

model = UrbanMLP()
model.load_state_dict(sd, strict=True)
model.eval()

# Test evaluation
with torch.no_grad():
    probs = model(torch.tensor(X_test)).numpy()
preds = np.argmax(probs, axis=1)

cm = confusion_matrix(y_test, preds)
class_names = ["Residential", "Commercial", "Industrial"]

print()
print("============================================")
print("   CONFUSION MATRIX (Test Set — 175 samples)")
print("============================================")
print(f"{'':>16}  {'Residential':>11}  {'Commercial':>10}  {'Industrial':>10}")
for i, name in enumerate(class_names):
    print(f"True {name:<12s}  {cm[i,0]:>7d}        {cm[i,1]:>7d}       {cm[i,2]:>7d}")

print()
print(classification_report(y_test, preds, target_names=class_names, digits=4))

print(f"Test accuracy:    {accuracy_score(y_test, preds):.4f}")
print(f"Weighted F1:      {f1_score(y_test, preds, average='weighted'):.4f}")
print(f"Macro F1:         {f1_score(y_test, preds, average='macro'):.4f}")

for i, name in enumerate(class_names):
    n = int(np.sum(y_test == i))
    p = precision_score(y_test, preds, labels=[i], average='micro', zero_division=0)
    r = recall_score(y_test, preds, labels=[i], average='micro', zero_division=0)
    f = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
    print(f"  {name:<12s} (n={n:3d})  prec={p:.4f}  recall={r:.4f}  f1={f:.4f}")

print()
# Save to file
import json
result = {
    "split_sizes": {"train": len(train_df), "val": len(val_df), "test": len(test_df)},
    "confusion_matrix": cm.tolist(),
    "class_names": class_names,
    "accuracy": float(accuracy_score(y_test, preds)),
    "weighted_f1": float(f1_score(y_test, preds, average='weighted')),
    "macro_f1": float(f1_score(y_test, preds, average='macro')),
}
os.makedirs("evals/validation", exist_ok=True)
with open("evals/validation/test_confusion_matrix.json", "w") as f:
    json.dump(result, f, indent=2)
print("Saved: evals/validation/test_confusion_matrix.json")
