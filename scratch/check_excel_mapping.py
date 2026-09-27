import pandas as pd
import re
import os

BASE_DIR = r"c:\Users\Atharv\OneDrive\Desktop\kcet rank predictor"
CLEAN_CSV = os.path.join(BASE_DIR, 'data', 'clean_data', 'kcet_cutoffs_clean.csv')
EXCEL_PATH = os.path.join(BASE_DIR, 'college_list', 'Karnataka_KCET_Engineering_Colleges.xlsx')

def get_clean_name(name):
    name = str(name).strip()
    name = re.split(r'\s+POST\s+BOX|\s+P\.?O\.?\s+BOX|\s+SURVEY\s+NO|\s+PIN\s+\d{5,6}|\s+NH\s+\d+', name, maxsplit=1, flags=re.IGNORECASE)[0].strip().rstrip(',')
    name = re.split(r',\s*(DAKSHINA|UTTARA|DIST|KARNATAKA|BENGALURU|BANGALORE|MYSURU|HUBBA|BELAGA|KOLAR|MANDYA|TUMKUR|BELLARY|GULBARGA|RAMANAGAR|CHITRADURGA|GADAG|KOPPAL|BIDAR|BELAGAVI|UDUPI|HASSAN|DAVENGERE|DAVANAGERE)', name, maxsplit=1, flags=re.IGNORECASE)[0].strip().rstrip(',')
    name = name.replace('Engg.', 'Engineering').replace('Engg', 'Engineering')
    name = re.sub(r'\s+', ' ', name).strip()
    
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
    if name in COLLEGE_MERGES:
        return COLLEGE_MERGES[name]
    name = re.sub(r'\s+(Bangalore|Mysore|Belgaum|Hubli|Mangalore|Davangere|Tumkur|Hassan|Gulbarga|Raihcur)$', '', name, flags=re.IGNORECASE).strip()
    return name

clean_df = pd.read_csv(CLEAN_CSV)
clean_colleges = set(get_clean_name(c) for c in clean_df['COLLEGE'].unique())
print(f"Total clean colleges in database: {len(clean_colleges)}")

excel_df = pd.read_excel(EXCEL_PATH)
print(f"Excel colleges: {len(excel_df)}")

# Let's clean the Excel college names and check matches
excel_mapping = {}
for _, row in excel_df.iterrows():
    ex_name = row['College Name']
    code = str(row['CET Code']).strip()
    clean_ex = get_clean_name(ex_name)
    excel_mapping[clean_ex] = {
        "cet_code": code,
        "full_name": ex_name
    }

matched = 0
missing = []
for c in clean_colleges:
    if c in excel_mapping:
        matched += 1
    else:
        missing.append(c)

print(f"Matched {matched} / {len(clean_colleges)} colleges using Excel mapping ({matched/len(clean_colleges)*100:.1f}%)")
print("Missing colleges from Excel list:")
for m in sorted(missing)[:15]:
    print(f"  - {m}")
