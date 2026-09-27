import pdfplumber
import os

BASE_DIR = r"c:\Users\Atharv\OneDrive\Desktop\kcet rank predictor"
PDF_PATH = os.path.join(BASE_DIR, 'data', 'raw_pdfs', '2025_kcet_eng_cutoffs_gen.pdf')

with pdfplumber.open(PDF_PATH) as pdf:
    # Page 2 (0-indexed page 1)
    page2 = pdf.pages[1]
    print("=== Page 2 Text Headings ===")
    text2 = page2.extract_text()
    print("\n".join(text2.split("\n")[:10]))
    
    tables2 = page2.extract_tables()
    print(f"\nFound {len(tables2)} tables on page 2")
    for idx, table in enumerate(tables2):
        print(f"\nTable {idx+1} rows:")
        for row in table[:15]:
            # Print first 2 columns (Course and some categories)
            if row:
                print(row[:15])
