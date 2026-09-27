import pdfplumber
import glob
import os
import re

BASE_DIR = r"c:\Users\Atharv\OneDrive\Desktop\kcet rank predictor"
RAW_PDF_DIR = os.path.join(BASE_DIR, 'data', 'raw_pdfs')

def extract_college_from_text(text):
    if not text:
        return None
    lines = text.strip().split('\n')
    for line in lines:
        line = line.strip()
        m = re.match(r'^College:\s*E?\d+\s+(.+)', line, re.IGNORECASE)
        if m:
            college = m.group(1).strip()
            college = re.split(r'\s*\(?\s*AUTONOMOUS\s*\)?\s*', college, maxsplit=1)[0].strip()
            college = re.split(r',\s*(?:Bangalore|Mysore|Hubli|Dharwad|Belgaum|Gulbarga|Mangalore|Bellary|Davangere|Shimoga|Hassan|Mandya|Tumkur|Raichur|Bidar|Bagalkot)', college, maxsplit=1, flags=re.IGNORECASE)[0].strip()
            college = college.rstrip(',').strip()
            return college
        m = re.match(r'^\d+\s+E\d+\s+(.+)', line)
        if m:
            college = m.group(1).strip()
            return college
    return None

pdf_files = sorted(glob.glob(os.path.join(RAW_PDF_DIR, '*_gen.pdf')))
for pdf_path in pdf_files:
    filename = os.path.basename(pdf_path)
    with pdfplumber.open(pdf_path) as pdf:
        matched = 0
        failed_lines = []
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            college = extract_college_from_text(text)
            if college:
                matched += 1
            else:
                first_line = text.split('\n')[0] if text else "EMPTY"
                if "college" in first_line.lower() or re.match(r'^\d+\s+E', first_line):
                    failed_lines.append((i+1, first_line))
        
        print(f"{filename:30s} | Pages: {len(pdf.pages):4d} | Matched Headings: {matched:4d}")
        if failed_lines:
            print("  Failed Heading Examples:")
            for p, line in failed_lines[:5]:
                print(f"    - Page {p}: {line}")
