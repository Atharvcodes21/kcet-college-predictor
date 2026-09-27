from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from schemas import PredictionRequest, CollegeResult, MetadataResponse
import pandas as pd
import numpy as np
import json
import os
import re

app = FastAPI(title="KCET Smart Option Entry Predictor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Paths ───────────────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.join(BASE_DIR, '..')
CLEAN_CSV = os.path.join(PROJECT_DIR, 'data', 'clean_data', 'kcet_cutoffs_clean.csv')
FRONTEND_DIR = os.path.join(PROJECT_DIR, 'frontend')
PRIORITY_JSON = os.path.join(BASE_DIR, 'college_priority.json')
PRIORITY_XLSX = os.path.join(PROJECT_DIR, 'college_list', 'Karnataka_KCET_Engineering_Colleges.xlsx')
PDF_INFO_JSON = os.path.join(BASE_DIR, 'college_pdf_info.json')

# ─── Globals (loaded once) ───────────────────────────────────────────────────────

cutoff_df: pd.DataFrame = None
course_list: list = []
category_list: list = []
data_year: int = 0
total_colleges: int = 0
college_priority: dict = {}   # college_name -> priority_rank (1 = best)
tier_map: dict = {}           # priority_rank -> tier label string
college_pdf_info: dict = {}   # college_name -> {"cet_code": code, "full_name": name}



# ─── Course Name Normalization ───────────────────────────────────────────────────

def fix_pdf_linebreaks(s: str) -> str:
    """Fix line-break artifacts from PDF extraction (e.g. 'DA TA' -> 'DATA')."""
    fixes = [
        ('COMMUNICATIO N', 'COMMUNICATION'), ('INSTRUMENTATI ON', 'INSTRUMENTATION'),
        ('INSTRUMENTATIO N', 'INSTRUMENTATION'), ('TELECOMMUNIC ATION', 'TELECOMMUNICATION'),
        ('TELECOMMUNICA TION', 'TELECOMMUNICATION'), ('ENVIRONMENTA L', 'ENVIRONMENTAL'),
        ('MANUFACTURIN G', 'MANUFACTURING'), ('ARTIFICIA L', 'ARTIFICIAL'),
        ('A RTIFICIAL', 'ARTIFICIAL'), ('AR TIFICIAL', 'ARTIFICIAL'),
        ('A RTIFICAL', 'ARTIFICIAL'), ('DA TA', 'DATA'), ('D ATA', 'DATA'),
        ('C YBER', 'CYBER'), ('CY BER', 'CYBER'), ('B LOCK', 'BLOCK'),
        ('BL OCK', 'BLOCK'), ('S OFTWARE', 'SOFTWARE'), ('SO FTWARE', 'SOFTWARE'),
        ('CLOU D', 'CLOUD'), ('V LSI', 'VLSI'), ('VLS I', 'VLSI'),
        ('DE V', 'DEV'), ('D EV', 'DEV'), ('PHARMACEUTIC AL', 'PHARMACEUTICAL'),
        ('INTERNE T', 'INTERNET'), ('I OT', 'IOT'), ('INTEGTATED', 'INTEGRATED'),
        ('COMMUNICATIO N', 'COMMUNICATION'), ('COMPUT ', 'COMPUTER '),
        ('COMPUTAR', 'COMPUTER'), ('ENGG.', 'ENGINEERING'), ('ENGG', 'ENGINEERING'),
    ]
    for old, new in fixes:
        s = s.replace(old, new)
    return s


def normalize_course(name: str) -> str:
    """Normalize course names to canonical form."""
    name = str(name).strip().upper()
    name = fix_pdf_linebreaks(name)

    # Strip degree prefixes
    for prefix in ['B TECH IN ', 'B.TECH IN ', 'BTECH IN ', 'B TECH ', 'B.TECH ']:
        if name.startswith(prefix):
            name = name[len(prefix):]
            break

    # Strip parenthetical line-break junk and re-fix
    name = fix_pdf_linebreaks(name)
    name = re.sub(r'\s+', ' ', name).strip()
    name = name.strip('.')

    # Canonical mapping for common abbreviations and variants
    CANON = {
        'CS': 'COMPUTER SCIENCE AND ENGINEERING', 'CE': 'CIVIL ENGINEERING',
        'ME': 'MECHANICAL ENGINEERING', 'EC': 'ELECTRONICS AND COMMUNICATION ENGINEERING',
        'EE': 'ELECTRICAL AND ELECTRONICS ENGINEERING', 'IS': 'INFORMATION SCIENCE AND ENGINEERING',
        'IT': 'INFORMATION TECHNOLOGY', 'BT': 'BIOTECHNOLOGY', 'AI': 'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING',
        'COMPUTERS': 'COMPUTER SCIENCE AND ENGINEERING', 'COMPUTER SCIENCE': 'COMPUTER SCIENCE AND ENGINEERING',
        'CSC': 'COMPUTER SCIENCE AND ENGINEERING', 'CIVIL': 'CIVIL ENGINEERING',
        'MECHANICAL': 'MECHANICAL ENGINEERING', 'ELECTRICAL': 'ELECTRICAL AND ELECTRONICS ENGINEERING',
        'ELECTRONICS': 'ELECTRONICS AND COMMUNICATION ENGINEERING', 'CHEMICAL': 'CHEMICAL ENGINEERING',
        'AUTOMOBILE': 'AUTOMOBILE ENGINEERING', 'TEXTILES': 'TEXTILE TECHNOLOGY',
        'ROBOTICS': 'ROBOTICS AND ARTIFICIAL INTELLIGENCE', 'MECHATRONICS': 'MECHATRONICS ENGINEERING',
        'INFO.SCIENCE': 'INFORMATION SCIENCE AND ENGINEERING', 'INFORMATION SCIENCE': 'INFORMATION SCIENCE AND ENGINEERING',
        'SILK TECH.': 'SILK TECHNOLOGY', 'POLYMER TECH.': 'POLYMER SCIENCE AND TECHNOLOGY',
        'MED.ELECT.': 'MEDICAL ELECTRONICS ENGINEERING', 'TELECOMMN.': 'TELECOMMUNICATION ENGINEERING',
        'IND. ENGG. MGMT.': 'INDUSTRIAL ENGINEERING AND MANAGEMENT',
        'IND.PRODN.': 'INDUSTRIAL AND PRODUCTION ENGINEERING',
        'ELEC. INST. ENGINEERING': 'ELECTRONICS AND INSTRUMENTATION ENGINEERING',
        'ELEC. TELECOMMN. ENGINEERING': 'TELECOMMUNICATION ENGINEERING',
        'CONST. TECH. MGMT.': 'CONSTRUCTION TECHNOLOGY AND MANAGEMENT',
        'BIO TECHNOLOGY': 'BIOTECHNOLOGY', 'BIO- TECHNOLOGY': 'BIOTECHNOLOGY',
        'BIO MEDICAL': 'BIOMEDICAL ENGINEERING', 'ENVIRONMENTAL': 'ENVIRONMENTAL ENGINEERING',
        'PLANNING': 'B.PLAN', 'B.PLAN': 'B.PLAN', 'DESIGN': 'DESIGN',
        'ARCHITECTURE': 'ARCHITECTURE', 'PRODUCTION ENGINEERING': 'PRODUCTION ENGINEERING',
        'CERAMICS': 'CERAMICS AND CEMENT ENGINEERING',
        'AERO SPACE ENGINEERING.': 'AEROSPACE ENGINEERING',
        'AERONAUT.ENGINEERING': 'AERONAUTICAL ENGINEERING',
        'AUTOMOTIVE ENGINEERING.': 'AUTOMOTIVE ENGINEERING',
    }

    if name in CANON:
        return CANON[name]

    # Normalize remaining patterns
    name = name.replace(' & ', ' AND ').replace('ENGINEERING(', 'ENGINEERING (')
    name = name.replace('ENGG (', 'ENGINEERING (').replace('ENGG.', 'ENGINEERING')
    name = re.sub(r'\s+', ' ', name).strip()

    return name


def normalize_college(name: str) -> str:
    """Normalize college names: strip addresses, merge duplicates, preserving CET code prefix."""
    name = str(name).strip()

    # Parse code prefix (e.g. "E003 - ")
    m = re.match(r'^(E\d+)\s*-\s*(.+)', name, re.IGNORECASE)
    if m:
        code = m.group(1).upper()
        rest = m.group(2).strip()
    else:
        code = ""
        rest = name

    # Remove long address suffixes
    rest = re.split(r'\s+POST\s+BOX|\s+P\.?O\.?\s+BOX|\s+SURVEY\s+NO|\s+PIN\s+\d{5,6}|\s+NH\s+\d+', rest, maxsplit=1, flags=re.IGNORECASE)[0].strip().rstrip(',')

    # Remove very long address tails
    rest = re.split(r',\s*(DAKSHINA|UTTARA|DIST|KARNATAKA|BENGALURU|BANGALORE|MYSURU|HUBBA|BELAGA|KOLAR|MANDYA|TUMKUR|BELLARY|GULBARGA|RAMANAGAR|CHITRADURGA|GADAG|KOPPAL|BIDAR|BELAGAVI|UDUPI|HASSAN|DAVENGERE|DAVANAGERE)', rest, maxsplit=1, flags=re.IGNORECASE)[0].strip().rstrip(',')

    # Standardize
    rest = rest.replace('Engg.', 'Engineering').replace('Engg', 'Engineering')
    rest = re.sub(r'\s+', ' ', rest).strip()

    # Specific merges for known duplicates
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

    # Trim trailing city names for cleanliness
    rest = re.sub(r'\s+(Bangalore|Mysore|Belgaum|Hubli|Mangalore|Davangere|Tumkur|Hassan|Gulbarga|Raihcur)$', '', rest, flags=re.IGNORECASE).strip()

    if code:
        return f"{code} - {rest}"
    return rest


# ─── Data Loading ────────────────────────────────────────────────────────────────

def load_data():
    """Load and normalize the clean cutoff CSV at startup."""
    global cutoff_df, course_list, category_list, data_year, total_colleges
    global college_priority, tier_map, college_pdf_info

    if not os.path.exists(CLEAN_CSV):
        print(f"ERROR: Clean CSV not found at {CLEAN_CSV}")
        return

    df = pd.read_csv(CLEAN_CSV)
    print(f"Loaded {len(df)} cutoff rows from CSV")

    # Normalize names
    df['COURSE_NAME'] = df['COURSE_NAME'].apply(normalize_course)
    df['COLLEGE'] = df['COLLEGE'].apply(normalize_college)

    # Use the latest year's data for predictions
    data_year = int(df['YEAR'].max())

    # For each college+course+category+sub_quota+region, keep latest year
    # If multiple rows exist after normalization, take minimum cutoff (most competitive)
    df_latest = df[df['YEAR'] == data_year].copy()
    df_latest = df_latest.groupby(
        ['COLLEGE', 'COURSE_NAME', 'CATEGORY', 'SUB_QUOTA', 'REGION'],
        as_index=False
    )['CUTOFF_RANK'].min()

    cutoff_df = df_latest
    course_list = sorted(cutoff_df['COURSE_NAME'].unique().tolist())
    category_list = sorted(cutoff_df['CATEGORY'].unique().tolist())
    total_colleges = cutoff_df['COLLEGE'].nunique()

    # ─── Load college priority ranking from JSON ─────────────────────────────
    if os.path.exists(PRIORITY_JSON):
        with open(PRIORITY_JSON, 'r') as f:
            college_priority = json.load(f)
        print(f"Loaded priority map: {len(college_priority)} colleges")
    else:
        print(f"WARNING: Priority JSON not found at {PRIORITY_JSON}")
        college_priority = {}

    # ─── Load PDF info mapping (original names & CET codes) ──────────────────
    if os.path.exists(PDF_INFO_JSON):
        try:
            with open(PDF_INFO_JSON, 'r') as f:
                college_pdf_info = json.load(f)
            print(f"Loaded PDF info map: {len(college_pdf_info)} colleges")
        except Exception as e:
            print(f"WARNING: Could not load PDF info map: {e}")
            college_pdf_info = {}
    else:
        print(f"WARNING: PDF info map not found at {PDF_INFO_JSON}")
        college_pdf_info = {}

    # ─── Load tier labels from Excel ─────────────────────────────────────────
    if os.path.exists(PRIORITY_XLSX):
        try:
            priority_df = pd.read_excel(PRIORITY_XLSX)
            tier_map = dict(zip(priority_df['Rank'].astype(int), priority_df['Tier']))
            print(f"Loaded tier map: {len(tier_map)} tiers")
        except Exception as e:
            print(f"WARNING: Could not load tier data from Excel: {e}")
            tier_map = {}
    else:
        print(f"WARNING: Priority Excel not found at {PRIORITY_XLSX}")
        tier_map = {}

    print(f"Data ready: {total_colleges} colleges, {len(course_list)} courses, year {data_year}")


# ─── Tier Fallback ───────────────────────────────────────────────────────────

TIER_RANGES = [
    (1, 10,  "Tier 1: Elite & Highly Competitive"),
    (11, 30, "Tier 2: Very Good & Well Established"),
    (31, 70, "Tier 3: Good & Established"),
    (71, 120, "Tier 4: Developing & Upcoming"),
    (121, 175, "Tier 5: Emerging"),
]


def get_tier_label(priority_rank: int) -> str:
    """Get tier label from tier_map (Excel) or fall back to hardcoded ranges."""
    if priority_rank in tier_map and tier_map[priority_rank]:
        return str(tier_map[priority_rank])
    # Fallback to range-based lookup
    for lo, hi, label in TIER_RANGES:
        if lo <= priority_rank <= hi:
            return label
    return ""  # unranked (999)


# Load data on import
load_data()


# ─── Static Files ────────────────────────────────────────────────────────────────

@app.get("/")
def serve_index():
    index = os.path.join(FRONTEND_DIR, 'index.html')
    if os.path.exists(index):
        return FileResponse(index)
    return {"message": "Frontend not found."}

if os.path.isdir(os.path.join(FRONTEND_DIR, 'css')):
    app.mount("/css", StaticFiles(directory=os.path.join(FRONTEND_DIR, 'css')), name="css")
if os.path.isdir(os.path.join(FRONTEND_DIR, 'js')):
    app.mount("/js", StaticFiles(directory=os.path.join(FRONTEND_DIR, 'js')), name="js")


# ─── Endpoints ───────────────────────────────────────────────────────────────────

@app.get("/metadata", response_model=MetadataResponse)
def get_metadata():
    if cutoff_df is None:
        raise HTTPException(status_code=503, detail="Data not loaded.")
    return MetadataResponse(
        courses=course_list,
        categories=category_list,
        total_colleges=total_colleges,
        data_year=data_year,
    )


@app.post("/predict", response_model=list[CollegeResult])
def check_admission(request: PredictionRequest):
    if cutoff_df is None:
        raise HTTPException(status_code=503, detail="Data not loaded.")

    user_rank = request.rank
    user_category = request.category
    user_courses = request.courses
    user_region = "HK" if request.is_hk_region else "General"

    # ─── Build all eligible (category, sub_quota) pools ─────────────────────
    # A reserved-category candidate is always also eligible for GM seats.
    eligible_categories = {user_category, 'GM'}

    # Sub-quotas: General is always included.
    # Rural candidates can also compete in Rural sub-quota pools.
    # Kannada Medium candidates can also compete in Kannada Medium pools.
    # NOTE: Both flags are mutually exclusive in KCET rules, but we handle both
    #       gracefully — whichever the user checks, that pool is added.
    eligible_sub_quotas = {'General'}
    if request.is_rural:
        eligible_sub_quotas.add('Rural')
    if request.is_kannada:
        eligible_sub_quotas.add('Kannada Medium')

    # ─── Filter by all eligible pools and region ─────────────────────────────
    mask = (
        (cutoff_df['CATEGORY'].isin(eligible_categories)) &
        (cutoff_df['SUB_QUOTA'].isin(eligible_sub_quotas)) &
        (cutoff_df['REGION'] == user_region)
    )

    # Filter by selected courses
    if user_courses:
        mask = mask & (cutoff_df['COURSE_NAME'].isin(user_courses))

    filtered = cutoff_df[mask].copy()

    if filtered.empty:
        return []

    # ─── Compute margin across all eligible pool rows ─────────────────────────
    # Positive margin means the student's rank is within the cutoff (can get in).
    filtered['margin'] = (filtered['CUTOFF_RANK'] - user_rank).astype(int)

    # Keep only rows where the student actually qualifies (rank <= cutoff)
    eligible = filtered[filtered['margin'] >= 0].copy()

    if eligible.empty:
        return []

    # ─── Per (college, course): pick the most lenient qualifying pool ─────────
    # "Most lenient" = highest cutoff rank (widest net). This is the pool where
    # the student fits most comfortably. If 3BR is missing but GMR has a higher
    # cutoff, the student qualifies under GMR — so we surface that pool.
    idx = eligible.groupby(['COLLEGE', 'COURSE_NAME'])['CUTOFF_RANK'].idxmax()
    best = eligible.loc[idx].copy()

    # ─── Assign college priority rank ────────────────────────────────────────
    best['priority_rank'] = best['COLLEGE'].map(
        lambda c: college_priority.get(re.sub(r'^E\d+\s*-\s*', '', c, flags=re.IGNORECASE), 999)
    )

    # Sort: best colleges first, then closest cutoff within same tier
    combined = best.sort_values(
        ['priority_rank', 'margin'],
        ascending=[True, True]
    )

    results = []
    for _, row in combined.iterrows():
        p_rank = int(row['priority_rank'])
        tier_label = get_tier_label(p_rank)

        # Build a human-readable label for which pool qualified
        pool_label = str(row['CATEGORY'])
        if row['SUB_QUOTA'] != 'General':
            pool_label += f" ({row['SUB_QUOTA']})"

        # Lookup PDF CET Code and Full Name
        pdf_info = college_pdf_info.get(row['COLLEGE'], {})
        cet_code = pdf_info.get('cet_code', '')
        college_full = pdf_info.get('full_name', row['COLLEGE'])

        results.append(CollegeResult(
            college=row['COLLEGE'],
            course=row['COURSE_NAME'],
            cutoff=int(row['CUTOFF_RANK']),
            year=data_year,
            can_get=True,
            margin=int(row['margin']),
            priority_rank=p_rank,
            tier=tier_label,
            qualifying_pool=pool_label,
            college_full=college_full,
            cet_code=cet_code,
        ))

    print(f"Query: rank={user_rank}, cat={user_category}, pools={eligible_categories}x{eligible_sub_quotas} -> {len(results)} eligible results")
    return results

# Trigger reload for prefix-aware data update.

