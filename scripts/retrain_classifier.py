"""
Retrain the UrbanMLP classifier from project.csv.
Reports full audit metrics and saves validated checkpoint.
"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset, WeightedRandomSampler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, classification_report

from app.infrastructure.ai_model import Embedder
from app.infrastructure.image_encoder import ImageEncoder
from app.domain.mlp_model import UrbanMLP
from app.config import POI_DIM, IMG_DIM, GRAPH_DIM, FUSION_DIM

LABEL_MAP = {"Residential": 0, "Commercial": 1, "Industrial": 2}
IDX_TO_LABEL = {0: "Residential", 1: "Commercial", 2: "Industrial"}
NUM_CLASSES = 3
DATA_PATH = "data/raw/project.csv"
CHECKPOINT_DIR = "models"
BEST_CHECKPOINT = os.path.join(CHECKPOINT_DIR, "urban_mlp_best.pt")
FINAL_CHECKPOINT = os.path.join(CHECKPOINT_DIR, "urban_mlp.pt")
METRICS_PATH = os.path.join(CHECKPOINT_DIR, "training_report.json")


def load_dataset():
    print(f"[AUDIT] Loading dataset from {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)
    df = df.dropna(subset=["label", "text_des"]).reset_index(drop=True)
    print(f"[AUDIT] Total samples: {len(df)}")
    print(f"[AUDIT] Label distribution:")
    label_counts = df["label"].value_counts().sort_index()
    for lbl, cnt in label_counts.items():
        label_name = IDX_TO_LABEL.get(int(lbl), f"Unknown-{lbl}")
        print(f"  {label_name} ({int(lbl)}): {cnt} ({cnt/len(df)*100:.1f}%)")
    class_weights = 1.0 / label_counts.values
    class_weights = class_weights / class_weights.sum() * NUM_CLASSES
    print(f"[AUDIT] Computed class weights: {class_weights}")
    return df, class_weights


def encode_features(df, modalities=None):
    if modalities is None:
        modalities = ["poi", "image", "graph"]

    print(f"[TRAIN] Encoding features with modalities={modalities}")
    poi_enc = Embedder() if "poi" in modalities else None
    img_enc = ImageEncoder() if "image" in modalities else None

    features = []
    labels = []
    valid_indices = []

    for idx, row in df.iterrows():
        parts = []

        if "poi" in modalities:
            text = str(row.get("text_des", "")).strip()
            if not text:
                continue
            poi_emb = np.asarray(poi_enc.embed_texts([text])[0], dtype=np.float32).reshape(-1)
            parts.append(poi_emb)

        if "image" in modalities:
            cell_id = row.get("cell_id", idx)
            img_path = os.path.join("data", "sat_images", f"cell_{cell_id}.png")
            if os.path.exists(img_path):
                try:
                    img_emb = np.asarray(img_enc.encode(img_path), dtype=np.float32).reshape(-1)
                except Exception:
                    img_emb = np.zeros(IMG_DIM, dtype=np.float32)
            else:
                img_emb = np.zeros(IMG_DIM, dtype=np.float32)
            parts.append(img_emb)

        if "graph" in modalities:
            graph_feat = np.array([0.0, 0.0, 0.0], dtype=np.float32)
            parts.append(graph_feat)

        fused = np.concatenate(parts).astype(np.float32)
        features.append(fused)
        labels.append(int(row["label"]))
        valid_indices.append(idx)

    X = np.array(features, dtype=np.float32)
    y = np.array(labels, dtype=np.int64)
    print(f"[TRAIN] Encoded {len(X)} valid samples")
    print(f"[TRAIN] Feature dim: {X.shape[1]}")
    return X, y


def train_model(X, y, class_weights, epochs=50, batch_size=32, lr=0.001):
    print(f"\n[TRAIN] Splitting data (test_size=0.2, stratify)")
    if len(np.unique(y)) >= 2 and len(y) >= 20:
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
    else:
        X_train, X_val, y_train, y_val = X, X, y, y

    print(f"[TRAIN] Train samples: {len(X_train)}, Val samples: {len(X_val)}")
    train_counts = pd.Series(y_train).value_counts().sort_index()
    for lbl, cnt in train_counts.items():
        print(f"  {IDX_TO_LABEL.get(int(lbl), lbl)}: {cnt}")
    val_counts = pd.Series(y_val).value_counts().sort_index()
    for lbl, cnt in val_counts.items():
        print(f"  Val-{IDX_TO_LABEL.get(int(lbl), lbl)}: {cnt}")

    X_train_t = torch.tensor(X_train, dtype=torch.float32)
    y_train_t = torch.tensor(y_train, dtype=torch.long)
    X_val_t = torch.tensor(X_val, dtype=torch.float32)
    y_val_t = torch.tensor(y_val, dtype=torch.long)

    class_weights_t = torch.tensor(class_weights, dtype=torch.float32)

    train_dataset = TensorDataset(X_train_t, y_train_t)
    val_dataset = TensorDataset(X_val_t, y_val_t)

    sample_weights = [class_weights[int(l)] for l in y_train]
    sampler = WeightedRandomSampler(sample_weights, len(sample_weights), replacement=True)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, sampler=sampler)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

    model = UrbanMLP(input_dim=X.shape[1], hidden_dim=256, output_dim=NUM_CLASSES)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    criterion = nn.CrossEntropyLoss(weight=class_weights_t)

    history = {
        "train_loss": [], "val_loss": [],
        "train_acc": [], "val_acc": [],
        "val_f1": [], "lr": lr, "epochs": epochs,
        "batch_size": batch_size, "input_dim": X.shape[1]
    }

    best_val_loss = float("inf")
    best_state = None
    patience = 10
    patience_counter = 0

    print(f"[TRAIN] Starting training for {epochs} epochs...")
    start_time = time.time()

    for epoch in range(epochs):
        model.train()
        train_loss = 0.0
        train_correct = 0
        train_total = 0

        for batch_x, batch_y in train_loader:
            optimizer.zero_grad()
            outputs = model(batch_x)
            loss = criterion(outputs, batch_y)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()

            train_loss += loss.item() * batch_x.size(0)
            _, preds = torch.max(outputs, 1)
            train_correct += (preds == batch_y).sum().item()
            train_total += batch_y.size(0)

        avg_train_loss = train_loss / train_total
        train_acc = train_correct / train_total

        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0
        all_val_preds = []
        all_val_labels = []

        with torch.no_grad():
            for batch_x, batch_y in val_loader:
                outputs = model(batch_x)
                loss = criterion(outputs, batch_y)
                val_loss += loss.item() * batch_x.size(0)
                _, preds = torch.max(outputs, 1)
                val_correct += (preds == batch_y).sum().item()
                val_total += batch_y.size(0)
                all_val_preds.extend(preds.cpu().numpy())
                all_val_labels.extend(batch_y.cpu().numpy())

        avg_val_loss = val_loss / val_total
        val_acc = val_correct / val_total
        val_f1 = f1_score(all_val_labels, all_val_preds, average="weighted")

        history["train_loss"].append(float(avg_train_loss))
        history["val_loss"].append(float(avg_val_loss))
        history["train_acc"].append(float(train_acc))
        history["val_acc"].append(float(val_acc))
        history["val_f1"].append(float(val_f1))

        if (epoch + 1) % 5 == 0 or epoch == 0:
            print(f"  Epoch {epoch+1:3d}/{epochs} | Train Loss: {avg_train_loss:.4f} Acc: {train_acc:.4f} | Val Loss: {avg_val_loss:.4f} Acc: {val_acc:.4f} F1: {val_f1:.4f}")

        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            best_state = model.state_dict()
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f"[TRAIN] Early stopping at epoch {epoch+1}")
                break

    elapsed = time.time() - start_time
    print(f"[TRAIN] Training completed in {elapsed:.1f}s")

    if best_state is not None:
        model.load_state_dict(best_state)

    # Final evaluation
    model.eval()
    with torch.no_grad():
        val_outputs = model(X_val_t)
        _, val_preds = torch.max(val_outputs, 1)
        val_preds_np = val_preds.cpu().numpy()
        val_labels_np = y_val_t.cpu().numpy()

    final_acc = accuracy_score(val_labels_np, val_preds_np)
    final_f1_weighted = f1_score(val_labels_np, val_preds_np, average="weighted")
    final_f1_macro = f1_score(val_labels_np, val_preds_np, average="macro")
    cm = confusion_matrix(val_labels_np, val_preds_np)

    print(f"\n[EVAL] Final Validation Results:")
    print(f"  Accuracy:  {final_acc:.4f}")
    print(f"  F1 (weighted): {final_f1_weighted:.4f}")
    print(f"  F1 (macro): {final_f1_macro:.4f}")
    print(f"  Confusion Matrix:")
    print(f"  {cm}")
    print(f"\n  Classification Report:")
    report = classification_report(val_labels_np, val_preds_np,
                                     target_names=[IDX_TO_LABEL[i] for i in range(NUM_CLASSES)])
    print(report)

    metrics = {
        "final_accuracy": float(final_acc),
        "final_f1_weighted": float(final_f1_weighted),
        "final_f1_macro": float(final_f1_macro),
        "confusion_matrix": cm.tolist(),
        "best_val_loss": float(best_val_loss),
        "training_time_seconds": float(elapsed),
        "train_samples": len(X_train),
        "val_samples": len(X_val),
    }
    metrics.update(history)

    return model, metrics


def save_checkpoints(model, metrics):
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)

    checkpoint = {
        "model_name": "urban_mlp",
        "input_dim": FUSION_DIM,
        "hidden_dim": 256,
        "output_dim": NUM_CLASSES,
        "state_dict": model.state_dict(),
        "label_map": LABEL_MAP,
        "idx_to_label": IDX_TO_LABEL,
        "metrics": {
            k: v for k, v in metrics.items()
            if k in ["final_accuracy", "final_f1_weighted", "final_f1_macro",
                     "best_val_loss", "training_time_seconds",
                     "train_samples", "val_samples"]
        }
    }

    torch.save(checkpoint, BEST_CHECKPOINT)
    print(f"[SAVE] Saved best checkpoint: {BEST_CHECKPOINT} ({os.path.getsize(BEST_CHECKPOINT)} bytes)")

    torch.save(checkpoint, FINAL_CHECKPOINT)
    print(f"[SAVE] Saved final checkpoint: {FINAL_CHECKPOINT} ({os.path.getsize(FINAL_CHECKPOINT)} bytes)")

    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2, default=str)
    print(f"[SAVE] Saved training report: {METRICS_PATH}")


def main():
    print("=" * 60)
    print("  URBAN CLASSIFIER RETRAINING PIPELINE")
    print("=" * 60)

    df, class_weights = load_dataset()
    X, y = encode_features(df, modalities=["poi", "image", "graph"])
    model, metrics = train_model(X, y, class_weights, epochs=50, batch_size=32, lr=0.001)
    save_checkpoints(model, metrics)

    print("\n" + "=" * 60)
    print("  RETRAINING COMPLETE")
    print(f"  Checkpoint: {FINAL_CHECKPOINT}")
    print(f"  Report: {METRICS_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    main()
