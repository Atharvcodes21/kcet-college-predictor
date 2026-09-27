"""Quick inspection of the extracted master CSV."""
import pandas as pd

df = pd.read_csv(r"c:\Users\Atharv\OneDrive\Desktop\kcet rank predictor\data\raw_csvs\master_raw.csv")
print("Shape:", df.shape)
print("\nColumns:", list(df.columns))
print("\nYEAR distribution:")
print(df['YEAR'].value_counts().sort_index())
print("\nQUOTA_TYPE distribution:")
print(df['QUOTA_TYPE'].value_counts())
print("\nSample rows:")
print(df[['COLLEGE', 'COURSE_NAME', 'GM', '1G', 'SCG', 'YEAR', 'QUOTA_TYPE']].head(10).to_string())
print("\nSample college names:")
for c in sorted(df['COLLEGE'].unique())[:15]:
    print(f"  {c}")
print("\nSample course names:")
for c in sorted(df['COURSE_NAME'].unique())[:15]:
    print(f"  {c}")
print(f"\nNon-null counts for key categories:")
for cat in ['GM', '1G', '2AG', '3AG', 'SCG', 'STG', 'GMK', 'GMR']:
    if cat in df.columns:
        count = df[cat].apply(lambda x: str(x) != '--' and str(x) != 'nan' and pd.notna(x)).sum()
        print(f"  {cat}: {count} values")
