import pdfplumber
import re
import os

BASE_DIR = r"c:\Users\Atharv\OneDrive\Desktop\kcet rank predictor"
PDF_PATH = os.path.join(BASE_DIR, 'data', 'raw_pdfs', '2025_kcet_eng_cutoffs_gen.pdf')

def extract_colleges_with_positions(page):
    """
    Extract all college headings on a page along with their vertical 'top' positions.
    Returns a list of dicts: [{'top': float, 'code': str, 'name': str}]
    """
    colleges = []
    # Extract text words/lines with positions
    # pdfplumber page.extract_text_lines() gives us text lines with 'top' coordinates
    lines = page.extract_text_lines()
    for line in lines:
        text = line['text'].strip()
        # Format 1: "College: E003 B M S College of Engineering, ..."
        m = re.match(r'^College:\s*(E\d+)\s+(.+)', text, re.IGNORECASE)
        if m:
            code = m.group(1).upper()
            name = m.group(2).strip()
            colleges.append({'top': line['top'], 'code': code, 'name': name})
            continue
        
        # Format 2: "1 E001 University Visveswariah..."
        m = re.match(r'^\d+\s+(E\d+)\s+(.+)', text)
        if m:
            code = m.group(1).upper()
            name = m.group(2).strip()
            colleges.append({'top': line['top'], 'code': code, 'name': name})
            continue
            
    return colleges

with pdfplumber.open(PDF_PATH) as pdf:
    page2 = pdf.pages[1] # Page 2
    
    colleges = extract_colleges_with_positions(page2)
    print("=== College Headings Found on Page 2 ===")
    for c in colleges:
        print(f"Top: {c['top']:6.2f} | Code: {c['code']} | Name: {c['name'][:60]}")
        
    tables = page2.find_tables()
    print(f"\nFound {len(tables)} tables on Page 2:")
    for idx, table in enumerate(tables):
        bbox = table.bbox # (x0, top, x1, bottom)
        print(f"Table {idx+1} BBox: {bbox}")
        
        # Find which college heading is closest above this table
        table_top = bbox[1]
        matching_college = None
        best_diff = float('inf')
        
        for c in colleges:
            if c['top'] < table_top:
                diff = table_top - c['top']
                if diff < best_diff:
                    best_diff = diff
                    matching_college = c
                    
        if matching_college:
            print(f"  -> Belongs to: {matching_college['code']} - {matching_college['name'][:60]} (diff: {best_diff:.2f})")
        else:
            print("  -> Belongs to: [No matching college above table]")
