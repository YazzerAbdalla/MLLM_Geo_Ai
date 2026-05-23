"""
 * Verification script for the multimodal dataset.
 * Prints row counts, class distributions, and null values for the spatial POI dataset.
"""
import os
import pandas as pd

def verify_dataset():
    """
     * Read the processed dataset and verify class distributions and data completeness.
     *
     * @returns {None}
    """
    # // Define dataset path
    csv_path = os.path.join("data", "raw", "project.csv")
    
    # // Ensure dataset exists
    if not os.path.exists(csv_path):
        print(f"Error: Dataset {csv_path} not found.")
        return

    # // Load the dataset
    print(f"--- Loading dataset from {csv_path} ---")
    df = pd.read_csv(csv_path)

    # // 1. Total row count
    row_count = len(df)
    print(f"Total Row Count: {row_count}")

    # // 2. Null values per column
    print("\nNull values count per column:")
    print(df.isnull().sum())

    # // 3. Class distribution
    print("\nClass (label) distribution:")
    if "label" in df.columns:
        print(df["label"].value_counts())
        
        # // Verify 3 distinct classes exist
        num_classes = df["label"].nunique()
        print(f"\nDistinct classes found: {num_classes}")
        if num_classes == 3:
            print("[OK] Three distinct classes found.")
        else:
            print("[ERROR] Dataset does not have exactly 3 classes.")
    else:
        print("[ERROR] 'label' column is missing in project.csv!")

if __name__ == "__main__":
    verify_dataset()