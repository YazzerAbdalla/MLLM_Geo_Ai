"""
 * Training script for UrbanMLP multi-modal model.
 """
import os
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import train_test_split
from app.infrastructure.ai_model import Embedder
from app.infrastructure.image_encoder import ImageEncoder
from app.domain.mlp_model import UrbanMLP
from app.config import POI_DIM, IMG_DIM, GRAPH_DIM

LABEL_MAP = {"Residential": 0, "Commercial": 1, "Industrial": 2}
FUSION_DIM = POI_DIM + IMG_DIM + GRAPH_DIM


def load_multimodal_features(df):
    poi_enc = Embedder()
    img_enc = ImageEncoder()

    features = []
    labels = []

    for idx, row in df.iterrows():
        poi_emb = poi_enc.embed_texts([row["text_description"]])[0]

        img_path = f"data/sat_images/cell_{idx}.png"
        if os.path.exists(img_path):
            img_emb = img_enc.encode(img_path)
        else:
            img_emb = torch.zeros(IMG_DIM).numpy()

        graph_emb = [0, 0, 0]

        combined = list(poi_emb) + list(img_emb) + graph_emb
        features.append(combined)
        labels.append(LABEL_MAP.get(row["label"], 0))

    return torch.tensor(features, dtype=torch.float32), torch.tensor(labels)


def train(epochs=100, batch_size=32, lr=0.001):
    data_path = "data/raw/project.csv"
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found")
        return

    print(f"Loading data from {data_path}...")
    df = pd.read_csv(data_path)
    df = df.dropna(subset=["label", "text_description"])

    train_df, _ = train_test_split(df, test_size=0.2, random_state=42)
    print(f"Training on {len(train_df)} samples...")

    print("Encoding multimodal features...")
    X, y = load_multimodal_features(train_df)

    dataset = TensorDataset(X, y)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    model = UrbanMLP(input_dim=FUSION_DIM)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()

    print(f"Training UrbanMLP for {epochs} epochs...")
    for epoch in range(epochs):
        model.train()
        total_loss = 0
        for batch_x, batch_y in loader:
            optimizer.zero_grad()
            loss = criterion(model(batch_x), batch_y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        if (epoch + 1) % 10 == 0:
            print(f"Epoch {epoch+1}/{epochs}, Loss: {total_loss/len(loader):.4f}")

    model_path = "models/urban_mlp.pt"
    os.makedirs("models", exist_ok=True)
    torch.save(model.state_dict(), model_path)
    print(f"Saved: {model_path}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=0.001)
    args = parser.parse_args()

    train(epochs=args.epochs, batch_size=args.batch_size, lr=args.lr)