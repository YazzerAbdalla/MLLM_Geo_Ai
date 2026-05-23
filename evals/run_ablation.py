import os
import json
import pandas as pd

# PATHS

BASELINE_RESULTS = "evals/baseline_results.json"
MULTIMODAL_RESULTS = "evals/multimodal_results.json"

OUTPUT_DIR = "evals/ablation_results"

os.makedirs(OUTPUT_DIR, exist_ok=True)


# LOAD RESULTS


with open(BASELINE_RESULTS, "r") as f:
    baseline_data = json.load(f)

with open(MULTIMODAL_RESULTS, "r") as f:
    multimodal_data = json.load(f)


# EXPERIMENT 1
# POI ONLY


poi_only = {
    "Experiment": "POI Only",
    "Accuracy": baseline_data.get("accuracy", 0),
    "Precision": baseline_data.get("f1_macro", 0),
    "Recall": baseline_data.get("f1_macro", 0),
    "F1-Score": baseline_data.get("f1_macro", 0),
    "Spatial Accuracy": "N/A"
}

# EXPERIMENT 2
# POI + IMAGE

poi_image = {
    "Experiment": "POI + Image",
    "Accuracy": multimodal_data.get("accuracy", 0),
    "Precision": multimodal_data.get("f1_macro", 0),
    "Recall": multimodal_data.get("f1_macro", 0),
    "F1-Score": multimodal_data.get("f1_macro", 0),
    "Spatial Accuracy": multimodal_data.get("spatial_accuracy", 0)
}

# EXPERIMENT 3
# FULL MODEL


full_model = {
    "Experiment": "Full Model",
    "Accuracy": multimodal_data.get("accuracy", 0),
    "Precision": multimodal_data.get("f1_macro", 0),
    "Recall": multimodal_data.get("f1_macro", 0),
    "F1-Score": multimodal_data.get("f1_macro", 0),
    "Spatial Accuracy": multimodal_data.get("spatial_accuracy", 0)
}

# SAVE INDIVIDUAL CSV FILES

pd.DataFrame([poi_only]).to_csv(
    os.path.join(OUTPUT_DIR, "poi_only_results.csv"),
    index=False
)

pd.DataFrame([poi_image]).to_csv(
    os.path.join(OUTPUT_DIR, "poi_image_results.csv"),
    index=False
)

pd.DataFrame([full_model]).to_csv(
    os.path.join(OUTPUT_DIR, "full_model_results.csv"),
    index=False
)

# COMPARISON TABLE

comparison_df = pd.DataFrame([
    poi_only,
    poi_image,
    full_model
])

comparison_df.to_csv(
    os.path.join(OUTPUT_DIR, "comparison_table.csv"),
    index=False
)

# PRINT RESULTS

print("\nAblation Study Completed Successfully!\n")
print(comparison_df)