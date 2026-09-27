import pdfplumber
import re
import os

BASE_DIR = r"c:\Users\Atharv\OneDrive\Desktop\kcet rank predictor"
PDF_PATH = os.path.join(BASE_DIR, 'data', 'raw_pdfs', '2024_kcet_gen.pdf')

def extract_all_colleges_from_page(page) -> list:
    colleges = []
    lines = page.extract_text_lines()
    print(f"Total layout lines found: {len(lines)}")
    # Print the first 10 lines to inspect them
    for idx, line in enumerate(lines[:10]):
        print(f"  Line {idx+1}: {line['text'].strip()!r}")
        
    for line in lines:
        text = line['text'].strip()
        m = re.match(r'^College:\s*(E\d+)\s+(.+)', text, re.IGNORECASE)
        if m:
            colleges.append({'code': m.group(1).upper(), 'full_name': m.group(2).strip()})
            continue
        m = re.match(r'^\d+\s+(E\d+)\s+(.+)', text)
        if m:
            colleges.append({'code': m.group(1).upper(), 'full_name': m.group(2).strip()})
            continue
    return colleges

with pdfplumber.open(PDF_PATH) as pdf:
    page2 = pdf.pages[1]
    colleges = extract_all_colleges_from_page(page2)
    print(f"\nExtracted colleges: {colleges}")
