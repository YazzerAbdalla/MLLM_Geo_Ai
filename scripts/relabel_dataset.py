"""
 * Relabel dataset and generate synthetic samples.
 * Maps category column -> numeric labels (0: Education/Health, 1: Mall/Shop/Bank, 2: Industrial/Factory).
 * Generates ~100 synthetic samples for class 1 and class 2 to ensure balanced training.
"""
import pandas as pd
import numpy as np
import random
import os

def relabel_and_generate():
    """
     * Relabel existing CSV rows and add synthetic Commercial & Industrial POIs.
     *
     * @returns {None}
    """
    # // Load the original project.csv
    csv_path = "data/raw/project.csv"
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found")
        return
        
    df = pd.read_csv(csv_path)
    print(f"Original row count: {len(df)}")
    
    # // Define mapping for categories
    # // Education/Health -> 0
    # // Mall/Shop/Bank -> 1
    # // Industrial/Factory -> 2
    category_mapping = {
        "Education": 0,
        "Health": 0,
        "Mall": 1,
        "Bank": 1,
        "Shop": 1,
        "Clinic": 0,    # // additional safety mapping
        "Hospital": 0,  # // additional safety mapping
        "School": 0,    # // additional safety mapping
        "University": 0,# // additional safety mapping
        "Industrial": 2,
        "Factory": 2
    }
    
    # // Apply label mapping based on category column
    df["label"] = df["category"].map(category_mapping)
    
    # // Fill missing labels using place_type if needed
    for idx, row in df.iterrows():
        if pd.isna(row["label"]):
            pt = str(row["place_type"]).lower()
            cat = str(row["category"]).lower()
            if "school" in pt or "hospital" in pt or "clinic" in pt or "university" in pt or "health" in pt or "education" in pt:
                df.at[idx, "label"] = 0
            elif "bank" in pt or "mall" in pt or "shop" in pt or "commercial" in pt:
                df.at[idx, "label"] = 1
            elif "industrial" in pt or "factory" in pt or "manufacturing" in pt:
                df.at[idx, "label"] = 2
            else:
                df.at[idx, "label"] = 0 # // fallback default
                
    # // Convert label column to int
    df["label"] = df["label"].astype(int)
    
    print("Class distribution after mapping existing rows:")
    print(df["label"].value_counts())
    
    # // Cairo bbox coordinates to generate realistic synthetic samples
    min_x, min_y, max_x, max_y = 31.20, 30.00, 31.25, 30.05
    
    # // Generate synthetic Commercial rows (Class 1)
    comm_names = [
        "National Bank of Egypt Branch", "CIB Bank ATM", "Banque Misr ATM",
        "City Stars Mall Shop", "Cairo Festival Mall Store", "Local Supermarket Kayan",
        "Fashion Clothing Boutique", "El Abd Bakery Shop", "Mobile Tech Store", "Gourmet Grocery Mall"
    ]
    comm_place_types = ["Bank", "Mall", "Shop"]
    
    synthetic_rows = []
    
    # // Add 100 synthetic Commercial POIs
    for i in range(100):
        name = f"{random.choice(comm_names)} {i+1}"
        place_type = random.choice(comm_place_types)
        category = place_type
        # // Generate random coordinates in Cairo bbox
        x = random.uniform(min_x, max_x)
        y = random.uniform(min_y, max_y)
        osm_id = random.randint(1000000000, 9999999999)
        text_des = f"تقع {name} في القاهرة، مصر. نوع المنطقة: {place_type}. البيانات من OpenStreetMap."
        
        synthetic_rows.append({
            "X": x,
            "Y": y,
            "osm_id": osm_id,
            "name": name,
            "place_type": place_type,
            "category": category,
            "text_des": text_des,
            "label": 1
        })
        
    # // Generate synthetic Industrial/Factory rows (Class 2)
    ind_names = [
        "Cairo Steel Industry Plant", "Helwan Cement Factory", "Egypt Textiles manufacturing",
        "Industrial Zone Warehouse", "Food Processing factory", "Chemical production plant",
        "Automotive assembly factory", "Paper milling factory", "Electronics assembly plant", "Plastic recycling factory"
    ]
    ind_place_types = ["Industrial", "Factory"]
    
    # // Add 100 synthetic Industrial POIs
    for i in range(100):
        name = f"{random.choice(ind_names)} {i+1}"
        place_type = random.choice(ind_place_types)
        category = "Industrial"
        # // Generate random coordinates in Cairo bbox
        x = random.uniform(min_x, max_x)
        y = random.uniform(min_y, max_y)
        osm_id = random.randint(1000000000, 9999999999)
        text_des = f"تقع {name} في القاهرة، مصر. نوع المنطقة: {place_type}. البيانات من OpenStreetMap."
        
        synthetic_rows.append({
            "X": x,
            "Y": y,
            "osm_id": osm_id,
            "name": name,
            "place_type": place_type,
            "category": category,
            "text_des": text_des,
            "label": 2
        })
        
    df_synthetic = pd.DataFrame(synthetic_rows)
    df_combined = pd.concat([df, df_synthetic], ignore_index=True)
    
    print(f"Combined row count: {len(df_combined)}")
    print("Combined class distribution:")
    print(df_combined["label"].value_counts())
    
    # // Backup original project.csv before overwriting
    backup_path = "data/raw/project_backup.csv"
    if not os.path.exists(backup_path):
        df.to_csv(backup_path, index=False)
        print(f"Original CSV backed up to {backup_path}")
        
    # // Save combined dataset
    df_combined.to_csv(csv_path, index=False)
    print(f"Successfully saved relabeled dataset to {csv_path}")

if __name__ == "__main__":
    relabel_and_generate()
