"""
Data Cleaning Pipeline for KCET Cutoff Data.

Takes the wide-format master CSV (from extract_pdfs.py) and produces
a clean long-format dataset ready for ML training.

Key transformations:
1. Melt wide category columns into long format (CATEGORY -> CUTOFF)
2. Normalize college & course names across years  
3. Tag regional quotas (Standard vs 371J)
4. Handle '--' and missing values
5. Normalize category codes to a clean taxonomy
"""

import pandas as pd
import numpy as np
import os
import re

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
RAW_CSV_DIR = os.path.join(BASE_DIR, 'data', 'raw_csvs')
CLEAN_DATA_DIR = os.path.join(BASE_DIR, 'data', 'clean_data')

# ─── Category Taxonomy ──────────────────────────────────────────────────────────
# Gen PDF columns:  1G, 1K, 1R, 2AG, 2AK, 2AR, 2BG, 2BK, 2BR, 
#                   3AG, 3AK, 3AR, 3BG, 3BK, 3BR,
#                   GM, GMK, GMP, GMR, NRI, OPN, OTH,
#                   SCG, SCK, SCR, STG, STK, STR
#
# HK PDF columns:   1H, 1KH, 1RH, 2AH, 2AKH, 2ARH, 2BH, 2BKH, 2BRH,
#                   3AH, 3AKH, 3ARH, 3BH, 3BKH, 3BRH,
#                   GMH, GMKH, GMPH, GMRH, 
#                   SCH, SCKH, SCRH, STH, STKH, STRH
#
# Strategy: 
#   - Columns ending in 'H' (from HK PDFs) -> Quota_Region = "HK"  
#   - Standard columns -> Quota_Region = "General"
#   - Base category extracted by removing the trailing 'G' or 'H' suffix

# Map raw column names to (base_category, sub_quota)
# Sub-quota: G=General, K=Kannada Medium, R=Rural, P=PH (disabled)
def parse_category_column(col_name: str) -> dict:
    """
    Parse a category column name into its components.
    Returns dict with: base_category, sub_quota, region
    """
    col = col_name.strip().upper()
    
    # Determine if HK region (column ends with H, from HK PDFs)
    # But be careful: GMH, SCH etc. end with H but base cat is GM, SC
    # The HK columns are: 1H, 2AH, 2BH, 3AH, 3BH, GMH, SCH, STH
    #                      1KH, 2AKH, 2BKH, 3AKH, 3BKH, GMKH, SCKH, STKH
    #                      1RH, 2ARH, 2BRH, 3ARH, 3BRH, GMRH, SCRH, STRH, GMPH
    
    # Standard Gen columns: 1G, 1K, 1R, 2AG, 2AK, 2AR, 2BG, 2BK, 2BR,
    #                       3AG, 3AK, 3AR, 3BG, 3BK, 3BR,
    #                       GM, GMK, GMP, GMR, SCG, SCK, SCR, STG, STK, STR
    #                       NRI, OPN, OTH
    
    # HK-specific columns all end with 'H' (but we need to distinguish from standard cols)
    # Actually the HK columns are specifically present in the HK PDF data
    # The simplest approach: if column name ends with 'H' AND isn't a standard gen column
    
    STANDARD_GEN_COLS = {
        '1G', '1K', '1R', 
        '2AG', '2AK', '2AR', 
        '2BG', '2BK', '2BR',
        '3AG', '3AK', '3AR', 
        '3BG', '3BK', '3BR',
        'GM', 'GMK', 'GMP', 'GMR',
        'SCG', 'SCK', 'SCR', 
        'STG', 'STK', 'STR',
        'NRI', 'OPN', 'OTH'
    }
    
    if col in STANDARD_GEN_COLS:
        region = 'General'
        # Determine sub_quota
        if col.endswith('K') and col != 'NRI':
            sub_quota = 'Kannada Medium'
        elif col.endswith('R') and col not in ('NRI', 'NR'):
            sub_quota = 'Rural'
        elif col.endswith('P') or col == 'GMP':
            sub_quota = 'PH'
        elif col in ('NRI', 'OPN', 'OTH'):
            sub_quota = col  # Keep as-is
        else:
            sub_quota = 'General'
        
        # Extract base category
        base = re.sub(r'[GKRP]$', '', col) if col not in ('GM', 'GMP', 'GMK', 'GMR', 'NRI', 'OPN', 'OTH') else col
        # Normalize base
        if base in ('', 'G') or col == 'GM':
            base = 'GM'
        elif col.startswith('GM'):
            base = 'GM'
        elif col.startswith('SC'):
            base = 'SC'
        elif col.startswith('ST'):
            base = 'ST'
        elif col.startswith('1'):
            base = 'Cat-1'
        elif col.startswith('2A'):
            base = '2A'
        elif col.startswith('2B'):
            base = '2B'
        elif col.startswith('3A'):
            base = '3A'
        elif col.startswith('3B'):
            base = '3B'
        
    else:
        # HK column 
        region = 'HK'
        # Strip trailing H to get equivalent gen column
        equiv = col.rstrip('H') if col.endswith('H') else col
        # Now parse as if gen
        if equiv.endswith('K'):
            sub_quota = 'Kannada Medium'
        elif equiv.endswith('R'):
            sub_quota = 'Rural'
        elif equiv.endswith('P') or equiv == 'GMP':
            sub_quota = 'PH'
        else:
            sub_quota = 'General'
        
        # Base category
        if equiv.startswith('GM') or equiv in ('', 'G'):
            base = 'GM'
        elif equiv.startswith('SC'):
            base = 'SC'
        elif equiv.startswith('ST'):
            base = 'ST'
        elif equiv.startswith('1'):
            base = 'Cat-1'
        elif equiv.startswith('2A'):
            base = '2A'
        elif equiv.startswith('2B'):
            base = '2B'
        elif equiv.startswith('3A'):
            base = '3A'
        elif equiv.startswith('3B'):
            base = '3B'
        else:
            base = equiv
    
    return {
        'raw_column': col_name,
        'base_category': base,
        'sub_quota': sub_quota,
        'region': region
    }


# ─── Course Name Normalization ──────────────────────────────────────────────────

# Map abbreviated course names (2021 format) to full names
COURSE_NORMALIZATION = {
    # 2021 format abbreviations
    'AI ARTIFICIAL INTELLIGENCE': 'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING',
    'CE CIVIL': 'CIVIL ENGINEERING',
    'CS COMPUTERS': 'COMPUTER SCIENCE AND ENGINEERING',
    'EC ELECTRONICS': 'ELECTRONICS AND COMMUNICATION ENGG',
    'EE ELECTRICAL': 'ELECTRICAL AND ELECTRONICS ENGINEERING',
    'IE INFO.SCIENCE': 'INFORMATION SCIENCE AND ENGINEERING',
    'ME MECHANICAL': 'MECHANICAL ENGINEERING',
    'BT BIO-TECH': 'BIO-TECHNOLOGY',
    'CH CHEMICAL': 'CHEMICAL ENGINEERING',
    'TX TEXTILES': 'TEXTILE TECHNOLOGY',
    'AU AUTOMOBILE': 'AUTOMOBILE ENGINEERING',
    'ST SILK TECH.': 'SILK TECHNOLOGY',
    'AE AERONAUT.ENGG': 'AERONAUTICAL ENGINEERING',
    'IM IND.ENGG & MGMT': 'INDUSTRIAL ENGINEERING AND MANAGEMENT',
    'IM IND.ENGG AND MGMT': 'INDUSTRIAL ENGINEERING AND MANAGEMENT',
    'IM IND. ENGG. MGMT.': 'INDUSTRIAL ENGINEERING AND MANAGEMENT',
    'AT AUTOMOTIVE ENGG.': 'AUTOMOTIVE ENGINEERING',
    'AM B TECH IN AM': 'ADDITIVE MANUFACTURING',
    'AD ARTIFICIAL INTEL, DATA SC': 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE',
    'AR ARCHITECTURE': 'ARCHITECTURE',
    'TC TELECOMMUNICATION': 'TELECOMMUNICATION ENGINEERING',
    'ML MACHINE LEARNING': 'MACHINE LEARNING',
    'IP INFO. SCIENCE': 'INFORMATION SCIENCE AND ENGINEERING',
    'MD MEDICAL ELECTRONICS': 'MEDICAL ELECTRONICS',
    'MN MINING': 'MINING ENGINEERING',
    'PT POLYMER TECH.': 'POLYMER SCIENCE AND TECHNOLOGY',
    'CY CYBER SECURITY': 'COMPUTER SCIENCE AND ENGINEERING (CYBER SECURITY)',
    'DS DATA SCIENCE': 'COMPUTER SCIENCE AND ENGINEERING(DATA SCIENCE)',
    'RO ROBOTICS': 'ROBOTICS AND ARTIFICIAL INTELLIGENCE',
    
    # Normalize inconsistencies across years
    'INDUSTRIAL ENGINEERING & MANAGEMENT': 'INDUSTRIAL ENGINEERING AND MANAGEMENT',
    'ELECTRICAL & ELECTRONICS ENGINEERING': 'ELECTRICAL AND ELECTRONICS ENGINEERING',
    'ELECTRONICS AND COMMUNICATION ENGINEERING': 'ELECTRONICS AND COMMUNICATION ENGG',
    'ELECTRONICS AND TELECOMMUNICATION ENGINEERING': 'ELECTRONICS AND TELECOMMUNICATION ENGG',
    'ELECTRONICS AND INSTRUMENTATION ENGINEERING': 'ELECTRONICS AND INSTRUMENTATION ENGG',
    'BIO-TECHNOLOGY': 'BIOTECHNOLOGY',
    'BIO- TECHNOLOGY': 'BIOTECHNOLOGY',
    'COMPUTER SCIENCE AND ENGG(ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING)': 
        'COMPUTER SCIENCE AND ENGINEERING (AI AND ML)',
    'COMPUTER SCIENCE AND ENGINEERING (CYBER SECURITY)': 
        'COMPUTER SCIENCE AND ENGINEERING (CYBER SECURITY)',
    'COMPUTER SCIENCE AND ENGINEERING(DATA SCIENCE)': 
        'COMPUTER SCIENCE AND ENGINEERING (DATA SCIENCE)',
    'AERO SPACE ENGINEERING': 'AEROSPACE ENGINEERING',
}

def normalize_course_name(name: str) -> str:
    """Normalize a course name for consistency across years."""
    name = str(name).strip().upper()
    # Remove leading code patterns like "CE ", "CS " etc.
    # These appear in 2021 format
    name = re.sub(r'^[A-Z]{2}\s+', '', name) if len(name) > 5 and name[2] == ' ' else name
    
    # Exact match first
    if name in COURSE_NORMALIZATION:
        return COURSE_NORMALIZATION[name]
    
    # Fuzzy normalization
    name = name.replace(' & ', ' AND ')
    name = re.sub(r'\s+', ' ', name)
    
    if name in COURSE_NORMALIZATION:
        return COURSE_NORMALIZATION[name]
    
    return name


def normalize_college_name(name: str) -> str:
    """Normalize college names by removing address details and standardizing."""
    name = str(name).strip()
    # Remove common address suffixes
    # Keep up to first comma or known city name
    # But preserve key identity parts
    
    # Remove leading/trailing spaces
    name = name.strip()
    
    # Truncate at common address delimiters (keep college name)
    # But be smart - don't truncate "R.V. College of Engineering"
    parts = re.split(r'\s+POST\s+BOX|\s+P\.?O\.?\s+BOX|\s+SURVEY\s+NO', name, maxsplit=1, flags=re.IGNORECASE)
    name = parts[0].strip().rstrip(',')
    
    # Standardize common abbreviations
    name = name.replace('Engg.', 'Engineering').replace('Engg', 'Engineering')
    name = re.sub(r'\s+', ' ', name)
    
    return name


# ─── Main Pipeline ──────────────────────────────────────────────────────────────

def clean_and_transform(master_csv_path: str = None) -> pd.DataFrame:
    """
    Full cleaning pipeline: wide-format master CSV -> long-format clean data.
    """
    if master_csv_path is None:
        master_csv_path = os.path.join(RAW_CSV_DIR, 'master_raw.csv')
    
    print("Loading master CSV...")
    df = pd.read_csv(master_csv_path, dtype=str)
    print(f"  Loaded {len(df)} rows, {len(df.columns)} columns")
    
    # Identify metadata vs category columns
    meta_cols = ['COLLEGE', 'COURSE_NAME', 'YEAR', 'QUOTA_TYPE']
    category_cols = [c for c in df.columns if c not in meta_cols]
    
    print(f"  Category columns ({len(category_cols)}): {category_cols}")
    
    # 1. Normalize college and course names
    print("\nNormalizing names...")
    df['COLLEGE'] = df['COLLEGE'].apply(normalize_college_name)
    df['COURSE_NAME'] = df['COURSE_NAME'].apply(normalize_course_name)
    
    # 2. Melt to long format
    print("Melting to long format...")
    long_df = pd.melt(
        df, 
        id_vars=meta_cols, 
        value_vars=category_cols,
        var_name='RAW_CATEGORY', 
        value_name='CUTOFF_RANK'
    )
    
    # 3. Drop missing/empty cutoffs
    long_df = long_df[long_df['CUTOFF_RANK'].notna()].copy()
    long_df = long_df[long_df['CUTOFF_RANK'] != '--'].copy()
    long_df = long_df[long_df['CUTOFF_RANK'] != ''].copy()
    long_df = long_df[long_df['CUTOFF_RANK'] != 'nan'].copy()
    
    # 4. Convert cutoff to numeric
    long_df['CUTOFF_RANK'] = pd.to_numeric(long_df['CUTOFF_RANK'], errors='coerce')
    long_df = long_df.dropna(subset=['CUTOFF_RANK']).copy()
    long_df['CUTOFF_RANK'] = long_df['CUTOFF_RANK'].astype(int)
    
    # 5. Parse category columns into structured fields
    print("Parsing categories...")
    parsed = long_df['RAW_CATEGORY'].apply(parse_category_column)
    long_df['CATEGORY'] = parsed.apply(lambda x: x['base_category'])
    long_df['SUB_QUOTA'] = parsed.apply(lambda x: x['sub_quota'])
    long_df['REGION'] = parsed.apply(lambda x: x['region'])
    
    # 6. For HK quota type PDFs, only keep HK region rows (avoid double-counting)
    # Gen PDFs have General region columns, HK PDFs have HK region columns
    # Since both gen and hk PDFs extract the SAME rows but different columns,
    # we need to filter: keep General region rows from gen PDFs, HK from hk PDFs
    before = len(long_df)
    long_df = long_df[
        ((long_df['QUOTA_TYPE'] == 'gen') & (long_df['REGION'] == 'General')) |
        ((long_df['QUOTA_TYPE'] == 'hk') & (long_df['REGION'] == 'HK'))
    ].copy()
    print(f"  Filtered quota alignment: {before} -> {len(long_df)} rows")
    
    # 7. Convert YEAR to int
    long_df['YEAR'] = long_df['YEAR'].astype(int)
    
    # 8. Drop duplicates
    long_df = long_df.drop_duplicates(
        subset=['COLLEGE', 'COURSE_NAME', 'CATEGORY', 'SUB_QUOTA', 'REGION', 'YEAR']
    ).copy()
    
    # 9. Select final columns
    final_df = long_df[[
        'YEAR', 'COLLEGE', 'COURSE_NAME', 'CATEGORY', 'SUB_QUOTA', 'REGION', 'CUTOFF_RANK'
    ]].sort_values(['YEAR', 'COLLEGE', 'COURSE_NAME', 'CATEGORY']).reset_index(drop=True)
    
    # Save clean data
    os.makedirs(CLEAN_DATA_DIR, exist_ok=True)
    clean_path = os.path.join(CLEAN_DATA_DIR, 'kcet_cutoffs_clean.csv')
    final_df.to_csv(clean_path, index=False)
    
    print(f"\n{'='*60}")
    print("CLEANING COMPLETE")
    print(f"  Total rows: {len(final_df)}")
    print(f"  Unique colleges: {final_df['COLLEGE'].nunique()}")
    print(f"  Unique courses: {final_df['COURSE_NAME'].nunique()}")
    print(f"  Categories: {sorted(final_df['CATEGORY'].unique())}")
    print(f"  Sub-quotas: {sorted(final_df['SUB_QUOTA'].unique())}")
    print(f"  Regions: {sorted(final_df['REGION'].unique())}")
    print(f"  Years: {sorted(final_df['YEAR'].unique())}")
    print(f"  Saved to: {clean_path}")
    print(f"{'='*60}")
    
    return final_df


if __name__ == "__main__":
    clean_and_transform()
