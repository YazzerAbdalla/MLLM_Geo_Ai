"""
Modality coverage audit script.
Counts non-zero image and graph features across the dataset.
"""
import os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

df = pd.read_csv('data/raw/project.csv')
df = df.dropna(subset=['label', 'text_des']).reset_index(drop=True)
total = len(df)

img_dir = 'data/sat_images'
img_count = 0

# Check what columns exist
cols = list(df.columns)
print("Columns in CSV:", cols)

has_node_count = 'node_count' in cols
has_total_length = 'total_length' in cols
has_avg_degree = 'avg_degree' in cols
has_cell_id = 'cell_id' in cols

graph_cols_exist = has_node_count and has_total_length and has_avg_degree

for idx, row in df.iterrows():
    cell_id = row.get('cell_id', idx)
    fname = f'data/sat_images/cell_{cell_id}.png'
    if os.path.exists(fname):
        img_count += 1

graph_nonzero = 0
graph_zero = 0
if graph_cols_exist:
    for idx, row in df.iterrows():
        nc = row.get('node_count', 0) if has_node_count else 0
        tl = row.get('total_length', 0.0) if has_total_length else 0.0
        ad = row.get('avg_degree', 0.0) if has_avg_degree else 0.0
        if nc != 0 or tl != 0.0 or ad != 0.0:
            graph_nonzero += 1
        else:
            graph_zero += 1
else:
    # graph columns don't exist - graph features are 100% synthetic/zero
    graph_nonzero = 0
    graph_zero = total

print(f"\n{'='*60}")
print(f"  MODALITY COVERAGE REPORT")
print(f"{'='*60}")
print(f"\n  Dataset: data/raw/project.csv")
print(f"  Total samples: {total}")
print(f"\n  --- Image Features ---")
print(f"  Samples with image files (non-zero): {img_count} ({img_count/total*100:.1f}%)")
print(f"  Samples without image files (zero):  {total-img_count} ({(total-img_count)/total*100:.1f}%)")

if graph_cols_exist:
    print(f"\n  --- Graph Features (from CSV columns) ---")
    print(f"  Graph columns found: node_count, total_length, avg_degree")
    print(f"  Samples with non-zero graph features: {graph_nonzero} ({graph_nonzero/total*100:.1f}%)")
    sample_rows = df[['node_count','total_length','avg_degree']].head(10) if has_node_count else pd.DataFrame()
    print(f"  Sample values (first 10):")
    for i, (_, row) in enumerate(df[['node_count','total_length','avg_degree']].head(10).iterrows()):
        print(f"    [{i}] node_count={row['node_count']}, total_length={row['total_length']}, avg_degree={row['avg_degree']}")
else:
    print(f"\n  --- Graph Features ---")
    print(f"  Graph columns (node_count, total_length, avg_degree) NOT in CSV")
    print(f"  Training scripts use hardcoded values:")
    print(f"    train_multimodal.py: graph=[2,1,0] (constant, non-zero but no information)")
    print(f"    retrain_classifier.py: graph=[0,0,0] (all zeros)")
    if not graph_cols_exist:
        graph_nonzero = total  # train_multimodal always sets [2,1,0]
        print(f"  Effective non-zero (train_multimodal): {graph_nonzero}/{total} (100%)")
        print(f"  Effective non-zero (retrain_classifier): 0/{total} (0%)")

print(f"\n  --- Modality Combinations (using retrain_classifier.py logic) ---")
print(f"  (POI always present for all valid samples)")
if graph_cols_exist:
    poionly = sum(1 for i, row in df.iterrows() if not os.path.exists(f'data/sat_images/cell_{row.get("cell_id", i)}.png') and (row.get('node_count',0)==0 and row.get('total_length',0.0)==0.0 and row.get('avg_degree',0.0)==0.0))
    imgpoi = sum(1 for i, row in df.iterrows() if os.path.exists(f'data/sat_images/cell_{row.get("cell_id", i)}.png') and (row.get('node_count',0)==0 and row.get('total_length',0.0)==0.0 and row.get('avg_degree',0.0)==0.0))
    graphpoi = sum(1 for i, row in df.iterrows() if not os.path.exists(f'data/sat_images/cell_{row.get("cell_id", i)}.png') and (row.get('node_count',0)!=0 or row.get('total_length',0.0)!=0.0 or row.get('avg_degree',0.0)!=0.0))
    allthree = sum(1 for i, row in df.iterrows() if os.path.exists(f'data/sat_images/cell_{row.get("cell_id", i)}.png') and (row.get('node_count',0)!=0 or row.get('total_length',0.0)!=0.0 or row.get('avg_degree',0.0)!=0.0))
else:
    poionly = sum(1 for i, row in df.iterrows() if not os.path.exists(os.path.join(img_dir, f'cell_{row.get("cell_id", i)}.png')))
    imgpoi = sum(1 for i, row in df.iterrows() if os.path.exists(os.path.join(img_dir, f'cell_{row.get("cell_id", i)}.png')))
    graphpoi = 0
    allthree = 0

print(f"  POI only (image=zeros, graph=zeros): {poionly} ({poionly/total*100:.1f}%)")
print(f"  Image + POI (graph=zeros):            {imgpoi} ({imgpoi/total*100:.1f}%)")
print(f"  Graph + POI (image only):             {graphpoi} ({graphpoi/total*100:.1f}%)")
print(f"  All three (image+graph+POI):          {allthree} ({allthree/total*100:.1f}%)")

print(f"\n  --- Assessment ---")
img_pct = img_count / total * 100
graph_pct = graph_nonzero / total * 100 if graph_cols_exist else 0
print(f"  Image coverage: {img_pct:.1f}%")
print(f"  Graph coverage: {graph_pct:.1f}% (retrain_classifier.py == {'real columns' if graph_cols_exist else 'hardcoded zeros'})")

if img_pct < 10:
    print(f"  >>> IMAGE COVERAGE BELOW 10% - model is effectively POI-only <<<")
elif graph_pct < 10:
    print(f"  >>> GRAPH COVERAGE BELOW 10% - model is effectively POI-only <<<")
else:
    print(f"  [OK] Both image and graph contribute meaningfully")

if img_pct < 10 or graph_pct < 10:
    print(f"  >>> VERDICT: MODEL IS EFFECTIVELY POI-ONLY <<<")
else:
    print(f"  >>> VERDICT: MODEL IS TRULY MULTIMODAL <<<")

print(f"{'='*60}")
