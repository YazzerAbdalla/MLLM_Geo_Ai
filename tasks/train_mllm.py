"""
 * Celery train_mllm task.
"""
import os

import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import TensorDataset, DataLoader
from sklearn.model_selection import train_test_split

from celery_app import celery_app
from app.infrastructure.ai_model import Embedder
from app.infrastructure.image_encoder import ImageEncoder
from app.domain.mlp_model import UrbanMLP


LABEL_MAP = {
    "Residential": 0,
    "Commercial": 1,
    "Industrial": 2,
}


def _encode_label(value):
    if isinstance(value, str):
        value = value.strip()
        if value not in LABEL_MAP:
            raise ValueError(f"Unknown label: {value}")
        return LABEL_MAP[value]
    return int(value)


@celery_app.task(bind=True)
def train_mllm_task(
    self,
    job_id: str,
    model_name: str,
    dataset_path: str,
    epochs: int = 3,
    batch_size: int = 8,
    learning_rate: float = 1e-3,
):
    from app.infrastructure.job_store import JobStore
    from celery.exceptions import Ignore

    store = JobStore()

    try:
        store.update_job(
            job_id,
            status="running",
            step="loading_dataset",
            progress=0.05,
            celery_task_id=self.request.id
        )

        if not os.path.exists(dataset_path):
            raise FileNotFoundError(f"Dataset not found: {dataset_path}")

        df = pd.read_csv(dataset_path)

        if "label" not in df.columns or "text_des" not in df.columns:
            raise ValueError("dataset must contain 'label' and 'text_des' columns")

        df = df.dropna(subset=["label", "text_des"]).reset_index(drop=True)

        if len(df) == 0:
            raise ValueError("Dataset is empty after dropping missing rows")

        store.update_job(
            job_id,
            step="preparing_features",
            progress=0.15
        )

        poi_enc = Embedder()
        img_enc = ImageEncoder()

        features = []
        labels = []

        for idx, row in df.iterrows():
            current_job = store.get_job(job_id) or {}
            if current_job.get("status") == "cancelled":
                raise Ignore()

            text = str(row.get("text_des", "")).strip()
            if not text:
                continue

            poi_emb = np.asarray(
                poi_enc.embed_texts([text])[0],
                dtype=np.float32
            ).reshape(-1)

            # Optional image path support
            img_path = row.get("image_path")
            if pd.isna(img_path) or not img_path:
                cell_id = row.get("cell_id", idx)
                img_path = os.path.join("data", "sat_images", f"cell_{cell_id}.png")

            if os.path.exists(str(img_path)):
                try:
                    img_emb = np.asarray(
                        img_enc.encode(str(img_path)),
                        dtype=np.float32
                    ).reshape(-1)
                except Exception:
                    img_emb = np.zeros(256, dtype=np.float32)
            else:
                img_emb = np.zeros(256, dtype=np.float32)

            graph_feat = np.array([0.0, 0.0, 0.0], dtype=np.float32)

            fused = np.concatenate([poi_emb, img_emb, graph_feat]).astype(np.float32)
            features.append(fused)
            labels.append(_encode_label(row["label"]))

        if not features:
            raise ValueError("No valid samples found for training")

        X = np.array(features, dtype=np.float32)
        y = np.array(labels, dtype=np.int64)

        num_classes = len(set(y.tolist()))

        store.update_job(
            job_id,
            step="splitting_data",
            progress=0.25
        )

        if len(X) >= 10:
            X_train, X_val, y_train, y_val = train_test_split(
                X, y,
                test_size=0.2,
                random_state=42,
                stratify=y if num_classes > 1 and len(y) >= num_classes * 2 else None
            )
        else:
            X_train, y_train = X, y
            X_val, y_val = X, y

        X_train_t = torch.tensor(X_train, dtype=torch.float32)
        y_train_t = torch.tensor(y_train, dtype=torch.long)

        train_loader = DataLoader(
            TensorDataset(X_train_t, y_train_t),
            batch_size=max(1, int(batch_size)),
            shuffle=True
        )

        input_dim = X.shape[1]
        hidden_dim = 256
        output_dim = 3  # Residential / Commercial / Industrial

        mlp = UrbanMLP(
            input_dim=input_dim,
            hidden_dim=hidden_dim,
            output_dim=output_dim
        )

        optimizer = torch.optim.Adam(mlp.parameters(), lr=float(learning_rate))
        criterion = nn.CrossEntropyLoss()

        store.update_job(
            job_id,
            step="training",
            progress=0.35
        )

        for epoch in range(int(epochs)):
            current_job = store.get_job(job_id) or {}
            if current_job.get("status") == "cancelled":
                raise Ignore()

            mlp.train()
            total_loss = 0.0

            for batch_X, batch_y in train_loader:
                optimizer.zero_grad()
                logits = mlp(batch_X)
                loss = criterion(logits, batch_y)
                loss.backward()
                optimizer.step()
                total_loss += float(loss.item())

            progress = 0.35 + ((epoch + 1) / max(1, int(epochs))) * 0.5
            store.update_job(
                job_id,
                step=f"epoch_{epoch + 1}/{epochs}",
                progress=round(progress, 4),
            )

        store.update_job(
            job_id,
            step="saving_model",
            progress=0.90
        )

        os.makedirs("data/models/trained", exist_ok=True)
        model_path = os.path.join(
            "data/models/trained",
            f"{model_name}_{job_id}.pt"
        )

        checkpoint = {
            "model_name": model_name,
            "input_dim": input_dim,
            "hidden_dim": hidden_dim,
            "output_dim": output_dim,
            "state_dict": mlp.state_dict(),
            "label_map": LABEL_MAP,
            "epochs": int(epochs),
            "batch_size": int(batch_size),
            "learning_rate": float(learning_rate),
        }

        torch.save(checkpoint, model_path)

        store.update_job(
            job_id,
            status="completed",
            step="done",
            progress=1.0,
            result_url=f"/api/v1/mllm/train-result/{job_id}",
            model_path=model_path
        )

    except Ignore:
        store.update_job(job_id, status="cancelled", step="cancelled")
        return

    except Exception as e:
        store.update_job(
            job_id,
            status="failed",
            error=str(e),
            step="failed"
        )
        raise