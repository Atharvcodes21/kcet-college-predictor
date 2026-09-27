import pdfplumber
import re
import os

BASE_DIR = r"c:\Users\Atharv\OneDrive\Desktop\kcet rank predictor"
PDF_PATH = os.path.join(BASE_DIR, 'data', 'raw_pdfs', '2025_kcet_eng_cutoffs_gen.pdf')

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

with pdfplumber.open(PDF_PATH) as pdf:
    print(f"Total pages in 2025 gen PDF: {len(pdf.pages)}")
    matched_count = 0
    for i, page in enumerate(pdf.pages):
        text = page.extract_text()
        college = extract_college_from_text(text)
        if college:
            matched_count += 1
            if "B M S" in college or "B.M.S" in college or "BMS" in college:
                print(f"Page {i+1} -> Matched: {college}")
        else:
            # Let's print the first line of text to see why it didn't match
            first_line = text.split('\n')[0] if text else "EMPTY"
            # Print page number and first line if it starts with College or numbers
            if "college" in first_line.lower() or re.match(r'^\d+\s+E', first_line):
                print(f"Page {i+1} -> FAILED TO MATCH heading: {first_line}")

    print(f"\nMatched headings on {matched_count} / {len(pdf.pages)} pages")
