import pdfplumber
import pandas as pd
import re
import os
import glob
import json

BASE_DIR = r"c:\Users\Atharv\OneDrive\Desktop\kcet rank predictor"
RAW_PDF_DIR = os.path.join(BASE_DIR, 'data', 'raw_pdfs')
CLEAN_CSV = os.path.join(BASE_DIR, 'data', 'clean_data', 'kcet_cutoffs_clean.csv')
OUTPUT_JSON = os.path.join(BASE_DIR, 'backend', 'college_pdf_info.json')

def extract_college_name_like_extract_pdfs(text):
    if not text:
        return None, None
    lines = text.strip().split('\n')
    for line in lines:
        line = line.strip()
        # Format 1: "College: E003 B M S College of Engineering, ..."
        m = re.match(r'^College:\s*(E\d+)\s+(.+)', line, re.IGNORECASE)
        if m:
            code = m.group(1).upper()
            college = m.group(2).strip()
            college = re.split(r'\s*\(?\s*AUTONOMOUS\s*\)?\s*', college, maxsplit=1)[0].strip()
            college = re.split(r',\s*(?:Bangalore|Mysore|Hubli|Dharwad|Belgaum|Gulbarga|Mangalore|Bellary|Davangere|Shimoga|Hassan|Mandya|Tumkur|Raichur|Bidar|Bagalkot)', college, maxsplit=1, flags=re.IGNORECASE)[0].strip()
            college = college.rstrip(',').strip()
            return code, college
        
        # Format 2: "1 E001 University Visveswariah..."
        m = re.match(r'^\d+\s+(E\d+)\s+(.+)', line)
        if m:
            code = m.group(1).upper()
            college = m.group(2).strip()
            return code, college
    return None, None

def get_clean_name(name):
    name = str(name).strip()
    m = re.match(r'^(E\d+)\s*-\s*(.+)', name, re.IGNORECASE)
    if m:
        code = m.group(1).upper()
        rest = m.group(2).strip()
    else:
        code = ""
        rest = name

    rest = re.split(r'\s+POST\s+BOX|\s+P\.?O\.?\s+BOX|\s+SURVEY\s+NO|\s+PIN\s+\d{5,6}|\s+NH\s+\d+', rest, maxsplit=1, flags=re.IGNORECASE)[0].strip().rstrip(',')
    rest = re.split(r',\s*(DAKSHINA|UTTARA|DIST|KARNATAKA|BENGALURU|BANGALORE|MYSURU|HUBBA|BELAGA|KOLAR|MANDYA|TUMKUR|BELLARY|GULBARGA|RAMANAGAR|CHITRADURGA|GADAG|KOPPAL|BIDAR|BELAGAVI|UDUPI|HASSAN|DAVENGERE|DAVANAGERE)', rest, maxsplit=1, flags=re.IGNORECASE)[0].strip().rstrip(',')
    rest = rest.replace('Engg.', 'Engineering').replace('Engg', 'Engineering')
    rest = re.sub(r'\s+', ' ', rest).strip()
    
    COLLEGE_MERGES = {
        'R. V. College of Engineering Bangalore': 'R.V. College of Engineering',
        'R. V. College of Engineering': 'R.V. College of Engineering',
        'B M S College of Engineering Basavanagudi,Bangalore': 'B.M.S. College of Engineering',
        'B M S College of Engineering, Basavanagudi': 'B.M.S. College of Engineering',
        'B M S College of Engineering': 'B.M.S. College of Engineering',
        'University Visveswariah College of Engineering Bangalore': 'UVCE Bangalore',
        'University of Visvesvaraya College of Engineering Bangalore': 'UVCE Bangalore',
        'University of Visvesvaraya College of Engineering Bangalore ( PUBLIC UNIV. )': 'UVCE Bangalore',
        'Univesity of Visvesvaraya College of Engineering (A State Autonomous Public University on IIT Model) K R Circle': 'UVCE Bangalore',
        'Sir M.Visvesvaraya Institute of Technology': 'Sir MVIT',
        'Sir M.Visveswaraya Institute of Technology Hunasemaranahalli,Bangalore': 'Sir MVIT',
        'M S Ramaiah Institute of Technology': 'M.S. Ramaiah Institute of Technology',
        'Siddaganga Institute of Technology Tumkur': 'Siddaganga Institute of Technology',
        'Siddaganga Institute of Technology': 'Siddaganga Institute of Technology',
    }
    if rest in COLLEGE_MERGES:
        rest = COLLEGE_MERGES[rest]
    rest = re.sub(r'\s+(Bangalore|Mysore|Belgaum|Hubli|Mangalore|Davangere|Tumkur|Hassan|Gulbarga|Raihcur)$', '', rest, flags=re.IGNORECASE).strip()
    
    if code:
        return f"{code} - {rest}"
    return rest

def extract_all_colleges_from_page(text) -> list:
    """Extract all college headings on a page with their full uncleaned names and codes."""
    colleges = []
    if not text:
        return colleges
    lines = text.strip().split('\n')
    for line in lines:
        line = line.strip()
        m = re.match(r'^College:\s*(E\d+)\s+(.+)', line, re.IGNORECASE)
        if m:
            colleges.append({'code': m.group(1).upper(), 'full_name': m.group(2).strip()})
            continue
        m = re.match(r'^\d+\s+(E\d+)\s+(.+)', line)
        if m:
            colleges.append({'code': m.group(1).upper(), 'full_name': m.group(2).strip()})
            continue
    return colleges

def main():
    print("Loading clean CSV unique colleges...")
    clean_df = pd.read_csv(CLEAN_CSV)
    clean_colleges = set()
    for col in clean_df['COLLEGE'].unique():
        clean_colleges.add(get_clean_name(col))
    print(f"Total unique normalized colleges in dataset: {len(clean_colleges)}")

    # Sort files to put 2025 first (latest has most mapped names)
    pdf_files = glob.glob(os.path.join(RAW_PDF_DIR, '*.pdf'))
    pdf_2025 = [f for f in pdf_files if '2025' in os.path.basename(f)]
    pdf_others = [f for f in pdf_files if '2025' not in os.path.basename(f)]
    
    # We will prioritize 2025
    ordered_pdfs = pdf_2025 + pdf_others
    print(f"Ordered PDFs to process: {[os.path.basename(f) for f in ordered_pdfs]}")
    
    mapping = {}

    for pdf_path in ordered_pdfs:
        filename = os.path.basename(pdf_path)
        
        # Check if we have already mapped all colleges
        mapped_colleges = set(mapping.keys())
        missing_colleges = clean_colleges - mapped_colleges
        if not missing_colleges:
            print("All colleges in cleaned CSV are already successfully mapped! Stopping early.")
            break
            
        print(f"Scanning headers of {filename} (still missing {len(missing_colleges)} colleges)...")
        
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                colleges = extract_all_colleges_from_page(text)
                for col in colleges:
                    code = col['code']
                    full_name = col['full_name']
                    clean_key = get_clean_name(f"{code} - {full_name}")
                    
                    # Store mapping if it's one of the colleges we care about
                    if clean_key in clean_colleges:
                        if clean_key not in mapping:
                            mapping[clean_key] = {
                                "cet_code": code,
                                "full_name": full_name
                            }
                        else:
                            # Keep longer name for details
                            if len(full_name) > len(mapping[clean_key]["full_name"]):
                                mapping[clean_key]["full_name"] = full_name
                            mapping[clean_key]["cet_code"] = code

    # Manual mapping fallbacks for any leftovers (if any)
    # UVCE Bangalore
    if "E001 - UVCE Bangalore" in clean_colleges and "E001 - UVCE Bangalore" not in mapping:
        mapping["E001 - UVCE Bangalore"] = {
            "cet_code": "E001",
            "full_name": "Univesity of Visvesvaraya College of Engineering (A State Autonomous Public University on IIT Model) K R Circle, Bangalore"
        }

    # Verify how many were mapped
    mapped_count = sum(1 for c in clean_colleges if c in mapping)
    print(f"\nMapped {mapped_count} out of {len(clean_colleges)} colleges ({mapped_count/len(clean_colleges)*100:.1f}%)")

    # Save mapping
    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    with open(OUTPUT_JSON, 'w') as f:
        json.dump(mapping, f, indent=2)
    print(f"\nSaved mapping to {OUTPUT_JSON}")

if __name__ == "__main__":
    main()
