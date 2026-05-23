"""
Training script for UrbanMLP multi-modal model.
"""

import sys, os, json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import train_test_split

from app.infrastructure.ai_model import Embedder
from app.infrastructure.image_encoder import ImageEncoder
from app.domain.mlp_model import UrbanMLP
from app.config import POI_DIM, IMG_DIM, GRAPH_DIM


def load_multimodal_features(df, modalities):
    poi_enc = Embedder() if "poi" in modalities else None
    img_enc = ImageEncoder() if "image" in modalities else None

    features, labels = [], []

    for idx, row in df.iterrows():
        combined = []

        if "poi" in modalities:
            poi_emb = poi_enc.embed_texts([row["text_des"]])[0]
            combined.extend(list(poi_emb))

        if "image" in modalities:
            img_path = f"data/sat_images/cell_{idx}.png"

            if os.path.exists(img_path):
                img_emb = img_enc.encode(img_path)
            else:
                img_emb = torch.zeros(IMG_DIM).numpy()

            combined.extend(list(img_emb))

        if "graph" in modalities:
            graph_emb = [2, 1, 0]
            combined.extend(graph_emb)

        features.append(combined)
        labels.append(int(row["label"]))

    return (
        torch.tensor(features, dtype=torch.float32),
        torch.tensor(labels, dtype=torch.long)
    )


def get_input_dim(modalities):
    dim = 0

    if "poi" in modalities:
        dim += POI_DIM
    if "image" in modalities:
        dim += IMG_DIM
    if "graph" in modalities:
        dim += GRAPH_DIM

    return dim


def train(epochs=100, batch_size=32, lr=0.001,
          modalities=["poi", "image", "graph"]):

    base_dir = os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )

    data_path = os.path.join(
        base_dir, "data", "raw", "project.csv"
    )

    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found")
        return

    print(f"Loading data from {data_path}...")
    print(f"Using modalities: {modalities}")

    df = pd.read_csv(data_path)
    df = df.dropna(subset=["label", "text_des"])

    train_df, val_df = train_test_split(
        df, test_size=0.2, random_state=42
    )

    print(f"Training on {len(train_df)} samples...")
    print(f"Validation on {len(val_df)} samples...")
    print("Encoding multimodal features...")

    X_train, y_train = load_multimodal_features(
        train_df, modalities
    )
    X_val, y_val = load_multimodal_features(
        val_df, modalities
    )

    train_loader = DataLoader(
        TensorDataset(X_train, y_train),
        batch_size=batch_size,
        shuffle=True
    )

    val_loader = DataLoader(
        TensorDataset(X_val, y_val),
        batch_size=batch_size,
        shuffle=False
    )

    input_dim = get_input_dim(modalities)
    model = UrbanMLP(input_dim=input_dim)

    optimizer = torch.optim.Adam(
        model.parameters(), lr=lr
    )

    criterion = nn.CrossEntropyLoss()

    history = {
        "train_loss": [],
        "val_loss": [],
        "val_accuracy": []
    }

    print(f"Training UrbanMLP for {epochs} epochs...")

    for epoch in range(epochs):
        model.train()
        total_train_loss = 0

        for batch_x, batch_y in train_loader:
            optimizer.zero_grad()

            outputs = model(batch_x)
            loss = criterion(outputs, batch_y)

            loss.backward()
            optimizer.step()

            total_train_loss += loss.item()

        avg_train_loss = total_train_loss / len(train_loader)

        model.eval()
        total_val_loss = 0
        correct, total = 0, 0

        with torch.no_grad():
            for batch_x, batch_y in val_loader:
                outputs = model(batch_x)

                loss = criterion(outputs, batch_y)
                total_val_loss += loss.item()

                _, predicted = torch.max(outputs, 1)

                total += batch_y.size(0)
                correct += (
                    predicted == batch_y
                ).sum().item()

        avg_val_loss = total_val_loss / len(val_loader)
        val_accuracy = correct / total

        history["train_loss"].append(avg_train_loss)
        history["val_loss"].append(avg_val_loss)
        history["val_accuracy"].append(val_accuracy)

        print(
            f"Epoch {epoch+1}/{epochs} | "
            f"Train Loss: {avg_train_loss:.4f} | "
            f"Val Loss: {avg_val_loss:.4f} | "
            f"Val Acc: {val_accuracy:.4f}"
        )

    os.makedirs("models", exist_ok=True)

    model_path = os.path.join(
        "models", "urban_mlp.pt"
    )

    torch.save(model.state_dict(), model_path)
    print(f"Saved: {model_path}")

    os.makedirs("evals", exist_ok=True)

    history_path = os.path.join(
        "evals", "training_history.json"
    )

    with open(history_path, "w") as f:
        json.dump(history, f, indent=4)

    print(f"Saved training history: {history_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=0.001)

    parser.add_argument(
        "--modalities",
        type=str,
        default="poi,image,graph"
    )

    args = parser.parse_args()

    modalities = [
        m.strip()
        for m in args.modalities.split(",")
    ]

    train(
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        modalities=modalities
    )