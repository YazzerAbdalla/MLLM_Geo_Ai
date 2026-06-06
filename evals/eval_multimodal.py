"""
 * Multi-modal evaluation script - MLP.
"""
import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
import numpy as np
import torch
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
from sklearn.model_selection import train_test_split

from app.infrastructure.ai_model import Embedder
from app.infrastructure.image_encoder import ImageEncoder
from app.domain.mlp_model import UrbanMLP


LABEL_MAP = {
    "Residential": 0,
    "Commercial": 1,
    "Industrial": 2
}

LABEL_INV = {v: k for k, v in LABEL_MAP.items()}

DATA_PATH = "data/raw/project.csv"
MODEL_PATH = "models/urban_mlp.pt"
OUTPUT_PATH = "evals/multimodal_results.json"


def compute_spatial_consistency(test_df, y_pred):
    """
    Compute spatial consistency as the proportion of cells whose predicted class
    agrees with the majority predicted class of their 8-neighborhood.
    """
    if not {"X", "Y"}.issubset(test_df.columns):
        print("Warning: X/Y columns not found")
        return 0.0

    directions = [
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)
    ]

    pred_map = {}
    coords = []

    for i in range(len(test_df)):
        x = int(round(test_df.loc[i, "X"]))
        y_coord = int(round(test_df.loc[i, "Y"]))
        coords.append((x, y_coord))
        pred_map[(x, y_coord)] = int(y_pred[i])

    consistent = 0
    total = 0

    for i, (x, y_coord) in enumerate(coords):
        neighbor_preds = []

        for dx, dy in directions:
            neighbor = (x + dx, y_coord + dy)
            if neighbor in pred_map:
                neighbor_preds.append(pred_map[neighbor])

        if not neighbor_preds:
            continue

        majority_neighbor = max(
            set(neighbor_preds),
            key=neighbor_preds.count
        )

        if int(y_pred[i]) == majority_neighbor:
            consistent += 1

        total += 1

    return consistent / total if total > 0 else 0.0


def main():
    if not os.path.exists(DATA_PATH):
        print(f"Error: {DATA_PATH} not found")
        return

    df = pd.read_csv(DATA_PATH)

    if "label" not in df.columns or "text_des" not in df.columns:
        print(f"Error: Required columns not found in {DATA_PATH}")
        return

    df = df.dropna(subset=["label", "text_des"])

    _, test_df = train_test_split(
        df,
        test_size=0.2,
        random_state=42
    )

    print(f"Testing on {len(test_df)} samples...")

    poi_enc = Embedder()
    img_enc = ImageEncoder()

    features = []
    y_true = []

    for idx, row in test_df.iterrows():
        text = row.get("text_des", "")
        if not text:
            continue

        poi_emb = poi_enc.embed_texts([text])[0]

        cell_idx = idx % 100
        img_path = f"data/sat_images/cell_{cell_idx}.png"

        # Don't skip sample if image missing
        if os.path.exists(img_path):
            img_emb = img_enc.encode(img_path)
        else:
            img_emb = np.zeros(256, dtype=np.float32)

        graph_f = np.array([0, 0, 0], dtype=np.float32)

        fused = np.concatenate([
            poi_emb,
            img_emb,
            graph_f
        ])

        features.append(fused)
        y_true.append(int(row.get("label", 0)))

    if not features:
        print("No features to evaluate")
        return

    X = torch.tensor(np.array(features), dtype=torch.float32)
    y = torch.tensor(y_true, dtype=torch.long)

    # Load model
    if not os.path.exists(MODEL_PATH):
        print("Training new UrbanMLP...")

        mlp = UrbanMLP(
            input_dim=643,
            hidden_dim=256,
            output_dim=3
        )

        optimizer = torch.optim.Adam(
            mlp.parameters(),
            lr=0.001
        )

        criterion = torch.nn.CrossEntropyLoss()

        for epoch in range(50):
            mlp.train()
            optimizer.zero_grad()

            output = mlp(X)
            loss = criterion(output, y)

            loss.backward()
            optimizer.step()

            if epoch % 10 == 0:
                print(f"Epoch {epoch}, Loss: {loss.item():.4f}")

        os.makedirs("models", exist_ok=True)

        torch.save(
            mlp.state_dict(),
            MODEL_PATH
        )

        print(f"Model saved to {MODEL_PATH}")
        mlp.eval()

    else:
        mlp = UrbanMLP(input_dim=643)
        mlp.load_state_dict(torch.load(MODEL_PATH, map_location="cpu"))
        mlp.eval()

    with torch.no_grad():
        probs = mlp(X).cpu().numpy()

    y_pred = probs.argmax(axis=1)

    # Standard metrics
    acc = accuracy_score(y_true, y_pred)

    f1 = f1_score(
        y_true,
        y_pred,
        average="macro"
    )

    f1_per = f1_score(
        y_true,
        y_pred,
        average=None
    )

    cm = confusion_matrix(
        y_true,
        y_pred
    )

    # ====================
    # AI-10 Spatial Consistency
    # 8-neighbor voting
    # ====================
    test_df = test_df.reset_index(drop=True)
    spatial_consistency = compute_spatial_consistency(test_df, y_pred)

    results = {
        "accuracy": round(float(acc), 4),
        "f1_macro": round(float(f1), 4),
        "f1_per_class": [
            round(float(x), 4)
            for x in f1_per
        ],
        "confusion_matrix": cm.tolist(),
        "spatial_consistency": round(
            float(spatial_consistency), 4
        )
    }

    os.makedirs("evals", exist_ok=True)

    with open(OUTPUT_PATH, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Multi-modal accuracy: {results['accuracy']}")
    print(f"Spatial consistency: {results['spatial_consistency']}")


if __name__ == "__main__":
    main()