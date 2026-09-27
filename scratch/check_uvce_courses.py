import pandas as pd
import os

BASE_DIR = r"c:\Users\Atharv\OneDrive\Desktop\kcet rank predictor"
CLEAN_CSV = os.path.join(BASE_DIR, 'data', 'clean_data', 'kcet_cutoffs_clean.csv')

df = pd.read_csv(CLEAN_CSV)

# Let's filter for UVCE (the one at KR Circle, Bangalore)
uvce = df[df['COLLEGE'].str.contains('Univesity of Visvesvaraya College of Engineering|UVCE Bangalore', case=False, na=False)]
print("Unique UVCE names matched:")
print(uvce['COLLEGE'].unique())

# Group by course name, year, category, sub_quota, region
latest_year = uvce['YEAR'].max()
print(f"\n--- UVCE Bangalore Cutoffs in Year {latest_year} ---")

# Let's pivot courses and categories to see which ones have GM, 3BG, 3BR, etc.
uvce_latest = uvce[uvce['YEAR'] == latest_year]

# Pivot table: Index = COURSE_NAME, Columns = (CATEGORY, SUB_QUOTA)
# Let's look at General region specifically
uvce_gen_region = uvce_latest[uvce_latest['REGION'] == 'General']
pivot = uvce_gen_region.pivot(index='COURSE_NAME', columns=['CATEGORY', 'SUB_QUOTA'], values='CUTOFF_RANK')

print("Pivot columns:")
print(pivot.columns)

# Let's print courses and check their 3B General vs 3B Rural vs GM General
subset = pivot.loc[:, [('GM', 'General'), ('3B', 'General'), ('3B', 'Rural')]]
print("\nCutoffs for courses at UVCE Bangalore (2025):")
print(subset)
