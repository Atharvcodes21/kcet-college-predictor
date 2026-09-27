import pandas as pd

CLEAN_CSV = r'data\clean_data\kcet_cutoffs_clean.csv'
df = pd.read_csv(CLEAN_CSV)
data_year = int(df['YEAR'].max())
df_latest = df[df['YEAR'] == data_year].groupby(
    ['COLLEGE','COURSE_NAME','CATEGORY','SUB_QUOTA','REGION'], as_index=False
)['CUTOFF_RANK'].min()

# ── test inputs ────────────────────────────────────────────────────────────────
user_rank     = 7000
user_category = '3B'
is_rural      = True
is_kannada    = False
user_region   = 'General'
user_courses  = ['ARTIFICIAL INTELLIGENCE AND DATA SCIENCE']

# ── NEW multi-pool logic ───────────────────────────────────────────────────────
eligible_categories = {user_category, 'GM'}
eligible_sub_quotas = {'General'}
if is_rural:   eligible_sub_quotas.add('Rural')
if is_kannada: eligible_sub_quotas.add('Kannada Medium')

mask = (
    df_latest['CATEGORY'].isin(eligible_categories) &
    df_latest['SUB_QUOTA'].isin(eligible_sub_quotas) &
    (df_latest['REGION'] == user_region) &
    df_latest['COURSE_NAME'].isin(user_courses)
)
filtered = df_latest[mask].copy()
filtered['margin'] = filtered['CUTOFF_RANK'] - user_rank

print('=== All pools checked for UVCE AIADS (rank=7000, 3B Rural) ===')
print(filtered[['COLLEGE','COURSE_NAME','CATEGORY','SUB_QUOTA','CUTOFF_RANK','margin']].to_string(index=False))
print()

eligible = filtered[filtered['margin'] >= 0].copy()

if not eligible.empty:
    idx = eligible.groupby(['COLLEGE','COURSE_NAME'])['CUTOFF_RANK'].idxmax()
    best = eligible.loc[idx].copy()
    for _, row in best.iterrows():
        pool = row['CATEGORY']
        if row['SUB_QUOTA'] != 'General':
            pool += f" ({row['SUB_QUOTA']})"
        print(f"RESULT:")
        print(f"  College : {row['COLLEGE'][:70]}")
        print(f"  Course  : {row['COURSE_NAME']}")
        print(f"  Pool    : {pool}")
        print(f"  Cutoff  : #{row['CUTOFF_RANK']:,}")
        print(f"  Margin  : +{int(row['margin']):,} ranks safe")
else:
    print('No eligible pools found.')
