"""
Extract tabular cutoff data from KEA KCET PDF files (2021-2025).

This module handles the messy reality of KEA PDF formats:
- College names appear as text subheadings above their tables
- Table column counts vary by year (2021 has 24 cats, 2025 has 28)
- Course names contain embedded newlines from PDF wrapping
- HK (Hyderabad-Karnataka / 371J) PDFs have fewer categories

Output: One CSV per PDF in data/raw_csvs/, plus a merged master CSV.
"""

import pdfplumber
import pandas as pd
import numpy as np
import re
import os
import glob


# ─── Constants ──────────────────────────────────────────────────────────────────

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
RAW_PDF_DIR = os.path.join(BASE_DIR, 'data', 'raw_pdfs')
RAW_CSV_DIR = os.path.join(BASE_DIR, 'data', 'raw_csvs')
CLEAN_DATA_DIR = os.path.join(BASE_DIR, 'data', 'clean_data')


# ─── Helpers ────────────────────────────────────────────────────────────────────

def clean_course_name(name: str) -> str:
    """Remove embedded newlines and extra whitespace from PDF-wrapped course names."""
    if not name:
        return ""
    cleaned = re.sub(r'\s*\n\s*', ' ', str(name))
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned.upper()


def extract_college_from_text(text: str) -> str | None:
    """
    Extract the college name from a page's raw text.
    
    Handles multiple KEA formats:
      - "College: E003 B M S College of Engineering, ..."
      - "1 E001 University Visveswariah College of Engineering Bangalore"
    """
    if not text:
        return None
    
    lines = text.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        # Format 1: "College: E003 ..."
        m = re.match(r'^College:\s*E?\d+\s+(.+)', line, re.IGNORECASE)
        if m:
            college = m.group(1).strip()
            # Remove trailing address info after the college name
            # Keep everything before "(AUTONOMOUS)" or the address
            college = re.split(r'\s*\(?\s*AUTONOMOUS\s*\)?\s*', college, maxsplit=1)[0].strip()
            # Remove trailing address portions (anything after a clear delimiter)
            college = re.split(r',\s*(?:Bangalore|Mysore|Hubli|Dharwad|Belgaum|Gulbarga|Mangalore|Bellary|Davangere|Shimoga|Hassan|Mandya|Tumkur|Raichur|Bidar|Bagalkot)', college, maxsplit=1, flags=re.IGNORECASE)[0].strip()
            college = college.rstrip(',').strip()
            return college
        
        # Format 2: "1 E001 University Visveswariah..."
        m = re.match(r'^\d+\s+E\d+\s+(.+)', line)
        if m:
            college = m.group(1).strip()
            return college
    
    return None


def extract_colleges_with_positions(page) -> list:
    """Extract all college headings on a page along with their vertical 'top' positions."""
    colleges = []
    lines = page.extract_text_lines()
    for line in lines:
        text = line['text'].strip()
        # Format 1: "College: E003 B M S College of Engineering, ..."
        m = re.match(r'^College:\s*(E\d+)\s+(.+)', text, re.IGNORECASE)
        if m:
            code = m.group(1).upper()
            college = m.group(2).strip()
            colleges.append({'top': line['top'], 'code': code, 'name': college})
            continue
        
        # Format 2: "1 E001 University Visveswariah..."
        m = re.match(r'^\d+\s+(E\d+)\s+(.+)', text)
        if m:
            code = m.group(1).upper()
            college = m.group(2).strip()
            colleges.append({'top': line['top'], 'code': code, 'name': college})
            continue
            
    return colleges


def extract_single_pdf(pdf_path: str) -> pd.DataFrame:
    """
    Extract all cutoff data from a single KEA PDF.
    
    Returns a wide-format DataFrame with columns:
    [COLLEGE, COURSE_NAME, cat1, cat2, ..., catN]
    """
    filename = os.path.basename(pdf_path)
    print(f"  Extracting: {filename}")
    
    all_rows = []
    current_college = None
    header_cols = None
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            # Extract all college headings with vertical positions on this page
            colleges = extract_colleges_with_positions(page)
            
            # Find and extract tables on this page
            tables = page.find_tables()
            
            for table_obj in tables:
                table = table_obj.extract()
                if not table or len(table) < 2:
                    continue
                
                # Find which college heading is closest above this table
                table_top = table_obj.bbox[1]
                matching_college = None
                best_diff = float('inf')
                
                for c in colleges:
                    if c['top'] < table_top:
                        diff = table_top - c['top']
                        if diff < best_diff:
                            best_diff = diff
                            matching_college = c
                
                if matching_college:
                    current_college = f"{matching_college['code']} - {matching_college['name']}"
                elif colleges:
                    current_college = f"{colleges[0]['code']} - {colleges[0]['name']}"
                
                # Process table rows
                for row in table:
                    if not row or all(c is None or str(c).strip() == '' for c in row):
                        continue
                    
                    first_cell = str(row[0]).strip() if row[0] else ''
                    
                    # Check if this is a header row
                    first_clean = re.sub(r'\s+', ' ', first_cell).upper()
                    if first_clean in ('COURSE NAME', 'COURSE\nNAME', '') or '1G' in first_clean:
                        # This is a header row - capture the category names
                        header_cols = [re.sub(r'\s+', '', str(c).strip()).upper() if c else '' for c in row[1:]]
                        continue
                    
                    # Otherwise this is a data row
                    if current_college and header_cols:
                        course_name = clean_course_name(first_cell)
                        if not course_name or course_name == '--':
                            continue
                        
                        values = row[1:]
                        row_dict = {
                            'COLLEGE': current_college,
                            'COURSE_NAME': course_name,
                        }
                        for i, cat in enumerate(header_cols):
                            if i < len(values) and cat:
                                val = str(values[i]).strip() if values[i] else '--'
                                # Clean embedded newlines in numbers
                                val = re.sub(r'\s*\n\s*', '', val)
                                row_dict[cat] = val
                        
                        all_rows.append(row_dict)
    
    if not all_rows:
        print(f"    [!] No data extracted from {filename}")
        return pd.DataFrame()
    
    df = pd.DataFrame(all_rows)
    print(f"    [OK] Extracted {len(df)} rows, {len(df['COLLEGE'].unique())} colleges")
    return df


def parse_year_and_type(filename: str) -> tuple[int, str]:
    """
    Parse year and quota type (gen/hk) from filename.
    Examples:
      '2021_kcet_gen.pdf' -> (2021, 'gen')
      '2024_kect_hk.pdf'  -> (2024, 'hk')
      '2025_kcet_eng_cutoffs_gen.pdf' -> (2025, 'gen')
    """
    name = filename.lower()
    
    year_match = re.search(r'(20\d{2})', name)
    year = int(year_match.group(1)) if year_match else 0
    
    if '_hk' in name:
        quota_type = 'hk'
    else:
        quota_type = 'gen'
    
    return year, quota_type


def extract_all_pdfs() -> pd.DataFrame:
    """
    Extract all PDFs in raw_pdfs/, save individual CSVs, and return a merged DataFrame.
    """
    os.makedirs(RAW_CSV_DIR, exist_ok=True)
    os.makedirs(CLEAN_DATA_DIR, exist_ok=True)
    
    pdf_files = sorted(glob.glob(os.path.join(RAW_PDF_DIR, '*.pdf')))
    
    if not pdf_files:
        raise FileNotFoundError(f"No PDF files found in {RAW_PDF_DIR}")
    
    print(f"\nFound {len(pdf_files)} PDF files to process:")
    for f in pdf_files:
        print(f"  - {os.path.basename(f)}")
    print()
    
    all_dfs = []
    
    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        year, quota_type = parse_year_and_type(filename)
        
        df = extract_single_pdf(pdf_path)
        
        if df.empty:
            continue
        
        # Add metadata columns
        df['YEAR'] = year
        df['QUOTA_TYPE'] = quota_type  # 'gen' or 'hk'
        
        # Save individual CSV
        csv_name = filename.replace('.pdf', '.csv')
        csv_path = os.path.join(RAW_CSV_DIR, csv_name)
        
        df.to_csv(csv_path, index=False)
        print(f"    -> Saved {csv_name}")
        
        all_dfs.append(df)
    
    if not all_dfs:
        raise ValueError("No data extracted from any PDF!")
    
    # Merge all DataFrames
    master_df = pd.concat(all_dfs, ignore_index=True, sort=False)
    
    # Save master CSV
    master_path = os.path.join(RAW_CSV_DIR, 'master_raw.csv')
    master_df.to_csv(master_path, index=False)
    
    print(f"\n{'='*60}")
    print(f"EXTRACTION COMPLETE")
    print(f"  Total rows: {len(master_df)}")
    print(f"  Unique colleges: {master_df['COLLEGE'].nunique()}")
    print(f"  Unique courses: {master_df['COURSE_NAME'].nunique()}")
    print(f"  Years covered: {sorted(master_df['YEAR'].unique())}")
    print(f"  Master CSV: {master_path}")
    print(f"{'='*60}")
    
    return master_df


if __name__ == "__main__":
    extract_all_pdfs()
