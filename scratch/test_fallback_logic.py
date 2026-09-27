import pandas as pd
import os

BASE_DIR = r"c:\Users\Atharv\OneDrive\Desktop\kcet rank predictor"
CLEAN_CSV = os.path.join(BASE_DIR, 'data', 'clean_data', 'kcet_cutoffs_clean.csv')

df = pd.read_csv(CLEAN_CSV)
latest_year = df['YEAR'].max()
df_latest = df[df['YEAR'] == latest_year].copy()

# UVCE college name
uvce_name = "Univesity of Visvesvaraya College of Engineering (A State Autonomous Public University on IIT Model) K R Circle"

# Test inputs
user_rank = 6000
user_category = "3B"
is_rural = True
is_kannada = False
user_region = "General"
user_courses = ["INFORMATION SCIENCE AND ENGINEERING", "COMPUTER SCIENCE AND ENGINEERING"]

# --- Simulation of Current Logic ---
print("=== CURRENT LOGIC ===")
# Determine single sub-quota
if is_kannada:
    user_sub_quota = "Kannada Medium"
elif is_rural:
    user_sub_quota = "Rural"
else:
    user_sub_quota = "General"

mask_curr = (
    (df_latest['COLLEGE'] == uvce_name) &
    (df_latest['COURSE_NAME'].isin(user_courses)) &
    (df_latest['CATEGORY'] == user_category) &
    (df_latest['SUB_QUOTA'] == user_sub_quota) &
    (df_latest['REGION'] == user_region)
)
filtered_curr = df_latest[mask_curr].copy()
print("Filtered rows with current logic:")
print(filtered_curr)

filtered_curr['margin'] = filtered_curr['CUTOFF_RANK'] - user_rank
eligible_curr = filtered_curr[filtered_curr['margin'] >= 0]
print("\nEligible courses found:")
print(eligible_curr[['COURSE_NAME', 'CUTOFF_RANK', 'margin']])


# --- Simulation of Improved Fallback Logic ---
print("\n=== IMPROVED FALLBACK LOGIC ===")
eligible_categories = {user_category, 'GM'}
eligible_sub_quotas = {'General'}
if is_rural:
    eligible_sub_quotas.add('Rural')
if is_kannada:
    eligible_sub_quotas.add('Kannada Medium')

mask_fallback = (
    (df_latest['COLLEGE'] == uvce_name) &
    (df_latest['COURSE_NAME'].isin(user_courses)) &
    (df_latest['CATEGORY'].isin(eligible_categories)) &
    (df_latest['SUB_QUOTA'].isin(eligible_sub_quotas)) &
    (df_latest['REGION'] == user_region)
)
filtered_fallback = df_latest[mask_fallback].copy()
print("All matching eligible quota rows for these courses:")
print(filtered_fallback[['COURSE_NAME', 'CATEGORY', 'SUB_QUOTA', 'CUTOFF_RANK']])

# Group by college & course, and select the row with the max CUTOFF_RANK
idx = filtered_fallback.groupby(['COLLEGE', 'COURSE_NAME'])['CUTOFF_RANK'].idxmax()
grouped_fallback = filtered_fallback.loc[idx].copy()
print("\nGrouped/Max-cutoff rows:")
print(grouped_fallback[['COURSE_NAME', 'CATEGORY', 'SUB_QUOTA', 'CUTOFF_RANK']])

grouped_fallback['margin'] = grouped_fallback['CUTOFF_RANK'] - user_rank
eligible_fallback = grouped_fallback[grouped_fallback['margin'] >= 0]
print("\nEligible courses found under fallback logic:")
print(eligible_fallback[['COURSE_NAME', 'CUTOFF_RANK', 'margin']])
