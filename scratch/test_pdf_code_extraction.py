import pdfplumber
import re
import os

BASE_DIR = r"c:\Users\Atharv\OneDrive\Desktop\kcet rank predictor"
PDF_PATH = os.path.join(BASE_DIR, 'data', 'raw_pdfs', '2025_kcet_eng_cutoffs_gen.pdf')

def test_extract_college(text):
    if not text:
        return None, None
    lines = text.strip().split('\n')
    for line in lines:
        line = line.strip()
        # Format 1: "College: E003 B M S College of Engineering, ..."
        m = re.match(r'^College:\s*(E\d+)\s+(.+)', line, re.IGNORECASE)
        if m:
            return m.group(1).upper(), m.group(2).strip()
        
        # Format 2: "1 E001 University Visveswariah..."
        m = re.match(r'^\d+\s+(E\d+)\s+(.+)', line)
        if m:
            return m.group(1).upper(), m.group(2).strip()
    return None, None

print("Opening PDF and testing first 10 pages...")
with pdfplumber.open(PDF_PATH) as pdf:
    for i in range(10):
        page = pdf.pages[i]
        text = page.extract_text()
        code, name = test_extract_college(text)
        print(f"Page {i+1} -> Code: {code} | Name: {name}")
