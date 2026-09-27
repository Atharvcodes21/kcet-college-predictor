"""Temporary analysis script to understand data distribution issues."""
import pandas as pd

df = pd.read_csv('data/clean_data/kcet_cutoffs_clean.csv')
print('Shape:', df.shape)
print('\nCutoff stats:')
print(df['CUTOFF_RANK'].describe())

print('\nCutoff histogram (percentiles):')
for p in [1, 5, 10, 25, 50, 75, 90, 95, 99]:
    print(f'  {p}th percentile: {df["CUTOFF_RANK"].quantile(p/100):.0f}')

print('\nSample colleges and cutoffs (sorted by median cutoff):')
sample = df.groupby('COLLEGE')['CUTOFF_RANK'].median().sort_values()
print('LOWEST cutoffs (top colleges):')
for c, v in list(sample.items())[:10]:
    print(f'  {v:>8.0f}  {c[:70]}')
print('HIGHEST cutoffs (easiest to get):')
for c, v in list(sample.items())[-10:]:
    print(f'  {v:>8.0f}  {c[:70]}')

print('\n\nCourse name uniqueness issue:')
courses = df['COURSE_NAME'].unique()
print(f'Total unique courses: {len(courses)}')
# Find duplicate-like courses
cse_like = [c for c in courses if 'COMPUTER' in c.upper() and 'SCIENCE' in c.upper()]
print(f'\nCSE-related courses ({len(cse_like)}):')
for c in sorted(cse_like)[:20]:
    count = len(df[df['COURSE_NAME'] == c])
    print(f'  [{count:>4} rows]  {c}')

# Check for colleges appearing with different names
print('\n\nBMS College variants:')
bms = [c for c in df['COLLEGE'].unique() if 'B M S' in c or 'BMS' in c]
for c in bms:
    count = len(df[df['COLLEGE'] == c])
    print(f'  [{count:>4} rows]  {c}')

print('\n\nRVCE variants:')
rv = [c for c in df['COLLEGE'].unique() if 'R. V.' in c or 'R V ' in c or 'RV ' in c]
for c in rv:
    count = len(df[df['COLLEGE'] == c])
    print(f'  [{count:>4} rows]  {c}')

# Check the cutoff for specific well-known college+course combos
print('\n\nRVCE CSE cutoffs by year:')
rvce_names = [c for c in df['COLLEGE'].unique() if 'R. V. College' in c or 'R V College' in c]
for name in rvce_names:
    sub = df[(df['COLLEGE'] == name) & 
             (df['COURSE_NAME'].str.contains('COMPUTER SCIENCE AND ENGINEERING', na=False)) &
             (df['CATEGORY'] == 'GM') &
             (df['SUB_QUOTA'] == 'General') &
             (df['REGION'] == 'General')]
    if len(sub) > 0:
        print(f'\n  {name}:')
        for _, row in sub.iterrows():
            print(f'    Year {row["YEAR"]}: Cutoff = {row["CUTOFF_RANK"]}')
