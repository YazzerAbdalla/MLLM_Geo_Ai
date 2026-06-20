"""
Generate 4 diagnostic plots:
  1. Confusion Matrix PNG
  2. Class Distribution PNG
  3. Training Loss Curve PNG
  4. Validation Loss Curve PNG
"""
import json, os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

plt.rcParams.update({"font.size": 12})

CLASS_NAMES = {0: "Residential", 1: "Commercial", 2: "Industrial"}
OUTPUT_DIR = "evals/plots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Load training report ──
with open("models/training_report.json") as f:
    report = json.load(f)

# ── Load dataset ──
df = pd.read_csv("data/raw/project.csv")
df = df.dropna(subset=["label"]).reset_index(drop=True)

# ══════════════════════════════════════════════════════════
# 1. CONFUSION MATRIX
# ══════════════════════════════════════════════════════════
cm = np.array(report["confusion_matrix"])
labels = [CLASS_NAMES[i] for i in range(3)]

fig, ax = plt.subplots(figsize=(6, 5))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
            xticklabels=labels, yticklabels=labels, ax=ax)
ax.set_xlabel("Predicted")
ax.set_ylabel("True")
ax.set_title("Confusion Matrix (Validation Set)")
fig.tight_layout()
fig.savefig(f"{OUTPUT_DIR}/confusion_matrix.png", dpi=150)
plt.close(fig)
print(f"  [OK] {OUTPUT_DIR}/confusion_matrix.png")

# ══════════════════════════════════════════════════════════
# 2. CLASS DISTRIBUTION
# ══════════════════════════════════════════════════════════
counts = df["label"].value_counts().sort_index()
labels_dist = [f"{CLASS_NAMES[i]}\n(label={i})" for i in counts.index]
values = counts.values
colors = sns.color_palette("Set2", len(values))

fig, ax = plt.subplots(figsize=(7, 5))
bars = ax.bar(labels_dist, values, color=colors, edgecolor="gray")
for bar, val in zip(bars, values):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
            str(val), ha="center", va="bottom", fontweight="bold")
ax.set_ylabel("Number of Samples")
ax.set_title(f"Class Distribution (Total: {len(df)})")
ax.set_ylim(0, max(values) * 1.15)
fig.tight_layout()
fig.savefig(f"{OUTPUT_DIR}/class_distribution.png", dpi=150)
plt.close(fig)
print(f"  [OK] {OUTPUT_DIR}/class_distribution.png")

# ══════════════════════════════════════════════════════════
# 3. TRAINING LOSS CURVE
# ══════════════════════════════════════════════════════════
train_loss = report["train_loss"]
epochs_t = list(range(1, len(train_loss) + 1))

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(epochs_t, train_loss, marker="o", linestyle="-",
        color="tab:blue", linewidth=1.5, markersize=4)
ax.set_xlabel("Epoch")
ax.set_ylabel("Training Loss")
ax.set_title("Training Loss Curve")
ax.grid(True, alpha=0.3)
ax.set_xlim(1, len(epochs_t))
fig.tight_layout()
fig.savefig(f"{OUTPUT_DIR}/training_loss_curve.png", dpi=150)
plt.close(fig)
print(f"  [OK] {OUTPUT_DIR}/training_loss_curve.png")

# ══════════════════════════════════════════════════════════
# 4. VALIDATION LOSS CURVE
# ══════════════════════════════════════════════════════════
val_loss = report["val_loss"]
epochs_v = list(range(1, len(val_loss) + 1))

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(epochs_v, val_loss, marker="s", linestyle="-",
        color="tab:red", linewidth=1.5, markersize=4)
ax.set_xlabel("Epoch")
ax.set_ylabel("Validation Loss")
ax.set_title("Validation Loss Curve")
ax.grid(True, alpha=0.3)
ax.set_xlim(1, len(epochs_v))
fig.tight_layout()
fig.savefig(f"{OUTPUT_DIR}/validation_loss_curve.png", dpi=150)
plt.close(fig)
print(f"  [OK] {OUTPUT_DIR}/validation_loss_curve.png")

print(f"\nAll 4 plots saved to {OUTPUT_DIR}/")
