"""
 * Training script for Random Forest baseline model.
 """
import os
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from app.infrastructure.ai_model import Embedder

LABEL_MAP = {"Residential": 0, "Commercial": 1, "Industrial": 2}


def train():
    data_path = "data/raw/project.csv"
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found")
        return

    print(f"Loading data from {data_path}...")
    df = pd.read_csv(data_path)
    df = df.dropna(subset=["label", "text_description"])

    train_df, _ = train_test_split(df, test_size=0.2, random_state=42)
    print(f"Training on {len(train_df)} samples...")

    print("Encoding text descriptions...")
    embedder = Embedder()
    X = embedder.embed_texts(train_df["text_description"].tolist())
    y = train_df["label"].map(LABEL_MAP).values

    print("Training Random Forest...")
    clf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    clf.fit(X, y)

    os.makedirs("models", exist_ok=True)
    model_path = "models/random_forest.pkl"
    joblib.dump(clf, model_path)
    print(f"Saved: {model_path}")


if __name__ == "__main__":
    train()