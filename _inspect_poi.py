"""Inspect POI data fields"""
import os, sys
os.environ["PYTHONIOENCODING"] = "utf-8"
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
df = pd.read_csv("data/raw/project.csv")
print("Columns:", list(df.columns))
print()
print("Unique place_types:", df["place_type"].dropna().unique()[:40])
print()
print("Unique categories:", df["category"].dropna().unique()[:40])
print()
print("Sample rows:")
for i in range(8):
    print(f"  [{i}] name={df['name'].iloc[i]}")
    print(f"       place_type={df['place_type'].iloc[i]}")
    print(f"       category={df['category'].iloc[i]}")
    print(f"       text_des={str(df['text_des'].iloc[i])[:200]}")
    print()
print("Category value counts (top 40):")
print(df["category"].value_counts().head(40))
print()
print("Place type value counts (top 40):")
print(df["place_type"].value_counts().head(40))
print()
# Cross-tab: category vs label
print("Category vs Label cross-tab:")
ct = pd.crosstab(df["category"], df["label"])
print(ct.head(40))
