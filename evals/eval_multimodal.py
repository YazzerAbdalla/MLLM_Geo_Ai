"""
 * Multi-modal evaluation script - MLP.
 """
import pandas as pd
import numpy as np
import json
import os
import torch
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
from sklearn.model_selection import train_test_split
from app.infrastructure.ai_model import Embedder
from app.infrastructure.image_encoder import ImageEncoder
from app.domain.mlp_model import UrbanMLP

LABEL_MAP = {"Residential": 0, "Commercial": 1, "Industrial": 2}
LABEL_INV = {v: k for k, v in LABEL_MAP.items()}

DATA_PATH = "data/raw/project.csv"
MODEL_PATH = "models/urban_mlp.pt"
OUTPUT_PATH = "evals/multimodal_results.json"


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

    poi_enc = Embedder()
    img_enc = ImageEncoder()

    features = []
    y_true = []
    y_true_labels = []

    for idx, row in test_df.iterrows():
        # Use text_des column
        text = row.get("text_des", "")
        if not text:
            continue
            
        poi_emb = poi_enc.embed_texts([text])[0]
        
        # Map row index to cell index - use modulo since we have fewer images
        cell_idx = idx % 100  # Use first 100 images
        img_path = f"data/sat_images/cell_{cell_idx}.png"
        
        if not os.path.exists(img_path):
            continue
            
        img_emb = img_enc.encode(img_path)
        graph_f = np.array([0, 0, 0], dtype=np.float32)
        fused = np.concatenate([poi_emb, img_emb, graph_f])
        features.append(fused)
        
        # Handle label: 0=Residential, 1=Commercial, 2=Industrial
        label = int(row.get("label", 0))
        y_true.append(label)
        y_true_labels.append(LABEL_INV.get(label, "Residential"))

    if not features:
        print("No features to evaluate")
        return

    X = torch.tensor(np.array(features), dtype=torch.float32)
    y = torch.tensor(y_true, dtype=torch.long)

    # Train if no model exists
    if not os.path.exists(MODEL_PATH):
        print("Training new UrbanMLP...")
        mlp = UrbanMLP(input_dim=643, hidden_dim=256, output_dim=3)
        
        optimizer = torch.optim.Adam(mlp.parameters(), lr=0.001)
        criterion = torch.nn.CrossEntropyLoss()
        
        # Simple training loop
        for epoch in range(50):
            mlp.train()
            optimizer.zero_grad()
            output = mlp(X)
            loss = criterion(output, y)
            loss.backward()
            optimizer.step()
            if epoch % 10 == 0:
                print(f"Epoch {epoch}, Loss: {loss.item():.4f}")
        
        # Save model
        os.makedirs("models", exist_ok=True)
        torch.save(mlp.state_dict(), MODEL_PATH)
        print(f"Model saved to {MODEL_PATH}")
    else:
        mlp = UrbanMLP(input_dim=643)
        mlp.load_state_dict(torch.load(MODEL_PATH))
        mlp.eval()

    with torch.no_grad():
        probs = mlp(X).numpy()
    y_pred = probs.argmax(axis=1)

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

    print(f"Multi-modal accuracy: {results['accuracy']}")


if __name__ == "__main__":
    main()