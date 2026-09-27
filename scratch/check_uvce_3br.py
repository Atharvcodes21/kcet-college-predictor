import pandas as pd
import os

BASE_DIR = r"c:\Users\Atharv\OneDrive\Desktop\kcet rank predictor"
CLEAN_CSV = os.path.join(BASE_DIR, 'data', 'clean_data', 'kcet_cutoffs_clean.csv')

df = pd.read_csv(CLEAN_CSV)
print("Columns in CSV:", df.columns)

# UVCE matches
uvce_rows = df[df['COLLEGE'].str.contains('Visvesvaraya|UVCE|E001', case=False, na=False)]
print(f"Total UVCE rows: {len(uvce_rows)}")
print("Unique UVCE college names:", uvce_rows['COLLEGE'].unique())

# Let's filter for UVCE and category 3B
uvce_3b = uvce_rows[uvce_rows['CATEGORY'] == '3B']
print(f"Total UVCE 3B rows: {len(uvce_3b)}")
print(uvce_3b.groupby(['YEAR', 'SUB_QUOTA', 'REGION']).size())

print("\nLet's print some sample rows for UVCE 3B:")
print(uvce_3b.head(20))

# Check for all categories at UVCE in year 2025 or latest year
latest_year = df['YEAR'].max()
print(f"\nUVCE cutoffs for latest year ({latest_year}):")
uvce_latest = uvce_rows[uvce_rows['YEAR'] == latest_year]
print(uvce_latest.groupby(['CATEGORY', 'SUB_QUOTA', 'REGION'])['CUTOFF_RANK'].count())
