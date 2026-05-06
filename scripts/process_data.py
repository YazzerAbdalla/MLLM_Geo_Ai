import pandas as pd

df = pd.read_csv('assets/project.csv')
df.rename(columns={
    'X': 'longitude',   # note: X is usually longitude
    'Y': 'latitude',    # Y is latitude
    'place type': 'place_type',
    'text_des': 'text_des'
}, inplace=True)

# Add a label column if missing – you need ground truth for classification.
# For now, you can create a dummy label (e.g., 0 for all) but later you must assign real classes.
# Example: Residential=0, Commercial=1, Industrial=2
df['label'] = 0  # placeholder

# Save to the expected location
df.to_csv('data/raw/project.csv', index=False)