"""
Build a college priority mapping from the Excel ranking sheet.
Maps normalized college names (from cutoff CSV after app.py normalization)
to their priority rank from the Excel sheet.

Strategy:
1. Manual mapping for top colleges and known tricky names
2. CET-code based matching where possible  
3. Keyword-based fuzzy matching for the rest
4. Unmatched colleges get a high default rank (999)
"""
import pandas as pd
import re
import json
import os

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.join(PROJECT_DIR, '..')


def normalize_college(name):
    """Same normalization as app.py"""
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


# ─── Manual mapping: normalized_college_name -> priority_rank ─────────────────
# This covers all the tricky cases where fuzzy matching fails.
# Format: substring of normalized name -> rank from Excel

MANUAL_MAPPING = {
    # Rank 1 - RVCE
    'R.V. College of Engineering': 1,
    'R V College of Engineering': 1,
    # Rank 2 - BMSCE
    'B.M.S. College of Engineering': 2,
    'B M S College of Engineering': 2,
    # Rank 3 - MSRIT
    'M.S. Ramaiah Institute of Technology': 3,
    'M S Ramaiah Institute of Technology': 3,
    # Rank 4 - PES Ring Road
    'PES University 100 Feet Ring Road': 4,
    'P E S College of Engineering Mandya': 72,  # Not PES Uni
    'P E S College of Engineering': 72,
    'P E S Institute of Technology': 4,
    # Rank 5 - UVCE
    'UVCE Bangalore': 5,
    'UVCE': 5,
    # Rank 6 - SJCE / JSS STU Mysuru
    'JSS Science and Technology University': 6,
    'Sri Jayachamarajendra College of Engineering': 6,
    # Rank 7 - NIE Mysuru
    'The National Institute of Engineering': 7,
    # Rank 8 - BIT
    'Bangalore Institute of Technology': 8,
    # Rank 9 - DSCE
    'Dayananda Sagar College of Engineering': 9,
    # Rank 10 - SIT Tumkur
    'Siddaganga Institute of Technology': 10,
    # Rank 11 - NMIT
    'Nitte Meenakshi Inst': 11,
    # Rank 12 - KLE Tech
    'KLE Technological University': 12,
    # Rank 13 - BMSIT
    'B M S Institute of Technology': 13,
    # Rank 14 - PES EC Campus
    'P E S University (Electronic City': 14,
    # Rank 15 - RNSIT
    'RNS Institute of Technology': 15,
    # Rank 16 - NHCE
    'New Horizon College of Engineering': 16,
    # Rank 17 - CMRIT
    'C M R Institute of Technology': 17,
    'CMR Institute of Technology': 17,
    # Rank 18 - Sir MVIT
    'Sir MVIT': 18,
    'Sir M.Visvesvaraya': 18,
    'Sir M.Visveswaraya': 18,
    # Rank 19 - BNMIT
    'B N M Institute of Technology': 19,
    # Rank 20 - JSSATE
    'J S S Academy of Technical Education': 20,
    # Rank 21 - Dr. AIT
    'Dr. Ambedkar Institute of Technology': 21,
    # Rank 22 - SDM Dharwad
    'S D M College of Engineering': 22,
    'SDM College of Engineering': 22,
    # Rank 23 - Global Academy
    'Global Academy of Technology': 23,
    # Rank 24 - Acharya
    'Acharya Institute of Technology': 24,
    # Rank 25 - Reva
    'Reva University': 25,
    'REVA University': 25,
    # Rank 26 - MVJ
    'M V J College of Engineering': 26,
    'MVJ College of Engineering': 26,
    # Rank 27 - NMAM
    'NMAM Institute of Technology': 27,
    'N.M.A.M Institute of Technology': 27,
    # Rank 28 - Oxford
    'The Oxford College of Engineering': 28,
    # Rank 29 - Sahyadri
    'Sahyadri College': 29,
    # Rank 30 - GIT Belagavi
    'K.L.S. Gogte Institute of Technology': 30,
    # Rank 31 - Malnad
    'Malnad College of Engineering': 31,
    # Rank 32 - SDM Ujire
    'S D M Institute of Tech': 32,
    'SDM Institute of Tech': 32,
    # Rank 33 - Bapuji
    'Bapuji Institute of Engineering': 33,
    # Rank 34 - PA College
    'P A College of Engineering': 34,
    # Rank 35 - Atria
    'Atria Institute of Technology': 35,
    # Rank 36 - K S School
    'K.S. School of Engineering': 36,
    # Rank 37 - AJ Institute
    'A J Institute of Engineering': 37,
    # Rank 38 - Canara
    'Canara Engineering College': 38,
    # Rank 39 - Don Bosco
    'DONBOSCO Institute of Technology': 39,
    # Rank 40 - GSSS Women
    'G S S S Institute of Engineering': 40,
    # Rank 41 - SJBIT
    'S J B Institute of Technology': 41,
    'S.J B. Institute of Technology': 41,
    # Rank 42 - City Engineering
    'City Engineering College': 42,
    # Rank 43 - SJC IT Chickballapur
    'S J C Institute of Technology': 43,
    # Rank 44 - KNS IT
    'K N S Institute of Technology': 44,
    # Rank 45 - MSEC
    'M S Engineering College': 45,
    # Rank 46 - Vidya Vikas
    'Vidya Vikas Institute of Engineering': 46,
    # Rank 47 - East Point
    'East Point College of Engineering': 47,
    # Rank 48 - DSATM
    'Dayananda Sagar Academy of Technology': 48,
    # Rank 49 - Sri Krishna IT
    'Sri Krishna Institute of Technology': 49,
    # Rank 50 - Cambridge
    'Cambridge Inst': 50,
    # Rank 51 - Sapthagiri
    'Sapthagiri College of Engineering': 51,
    # Rank 52 - Sri Siddhartha IT
    'Sri Siddartha Institute of Technology': 52,
    'Sri Siddhartha Institute of Technology': 52,
    # Rank 53 - Brindavan
    'Brindavan College of Engineering': 53,
    # Rank 54 - East West
    'East West Institute of Technology': 54,
    'East West Institute Of Technology': 54,
    # Rank 55 - SJMIT
    'S J M Institute of Technology': 55,
    # Rank 56 - Angadi
    'Angadi Institute of Technology': 56,
    # Rank 57 - Vemana
    'Vemana Institute of Technology': 57,
    # Rank 58 - HKBK
    'H.K.B.K.College of Engineering': 58,
    # Rank 59 - Navadaya
    'Navodaya Institute of Technology': 59,
    # Rank 60 - Rajarajeswari
    'Rajarajeswari College of Engineering': 60,
    # Rank 61 - HMS IT
    'H M S Institute of Technology': 61,
    # Rank 62 - MITE Mangalore
    'Mangalore Institute of Technology and Engineering': 62,
    # Rank 63 - KS IT Raghuvanahalli
    'K S Institute of Technology': 63,
    # Rank 64 - RR CE
    'R.L.Jalappa Institute of Technology': 64,
    # Rank 65 - Sai Vidya
    'Sai Vidya Institute of Technology': 65,
    # Rank 66 - T John
    'T John Institute of Technology': 66,
    'T.John Institute of technology': 66,
    # Rank 67 - Alva's
    "Alva`s Institute of Engineering": 67,
    # Rank 68 - AMC
    'AMC Engineering College': 68,
    # Rank 69 - St Joseph
    'St. Joseph Engineering College': 69,
    'St.Joseph Engineering College': 69,
    # Rank 70 - Basaveshwara Bagalkot
    'Basaveshwara Engineering College': 70,
    'B V V Sangha': 70,
    # Rank 71 - SMVIT
    'Shri Madhwa Vadiraja Institute of Technology': 71,
    # Rank 73 - Srinivas IT
    'Srinivas Institute of Technology': 73,
    # Rank 74 - Sambhram
    'Sambhram Institute of Technology': 74,
    # Rank 75 - KVG Sullia
    'K V G College of Engineering': 75,
    # Rank 76 - Tontadarya
    'Tontadarya College of Engineering': 76,
    # Rank 77 - BCT Davangere
    'Bheemanna Khandre': 77,
    # Rank 78 - Guru Nanak Dev
    'Gurunanak Dev Engineering College': 78,
    # Rank 79 - Maratha Mandal
    'Maratha Mandal Engineering College': 79,
    # Rank 80 - Proudadevaraya
    'Proudadevaraya Institute of Technology': 80,
    # Rank 81 - Coorg IT
    'Coorg Institute of Technology': 81,
    # Rank 82 - CMR University
    'CMR University': 82,
    # Rank 83 - BGS College
    'BGS College of Engineering': 83,
    # Rank 84 - SEA College
    'S E A College of Engineering': 84,
    # Rank 85 - KCT
    'K C T Engineering College': 85,
    # Rank 86 - Impact
    'Impact College of Engineering': 86,
    # Rank 87 - Maharaja IT Mysore
    'Maharaja Institute of Technology': 87,
    # Rank 88 - Sri Venkateshwara
    'Sri Venkateshwara College of Engineering': 88,
    # Rank 89 - KLE Dr MS Sheshagiri
    'KLE Technological University(Formerly KLE Dr.MS': 89,
    # Rank 90 - University BDT
    'University B.D.T': 90,
    # Rank 91 - Adhichunchanagiri
    'Adhichunchanagiri Institute of Technology': 91,
    'Adichunchanagiri University': 91,
    # Rank 92 - Bahubali
    'Bahubali College of Engineering': 92,
    # Rank 93 - Sri Taralabalu
    'Sri Taralabalu Jagadguru': 93,
    # Rank 94 - Vivekananada
    'Vivekananada': 94,
    # Rank 95 - Anjuman
    'Anjuman': 95,
    # Rank 96 - Ballari IT
    'Ballari Institute of Technology': 96,
    # Rank 97 - Basavakalyana
    'Basavakalyana Engineering College': 97,
    # Rank 98 - UBDT
    'University B.D.T College of Engineering': 98,
    # Rank 99 - Shridevi
    'Shridevi Institute of Engineering': 99,
    'Shreedevi Institute of Technology': 99,
    # Rank 100 - KLE IT
    'K L E Institute of Technology': 100,
    # Rank 101 - Hira Sugar
    'Hira Sugar Institute of Technology': 101,
    # Rank 102 - Nagarjuna
    'Nagarjuna College of Engineering': 102,
    # Rank 103 - G Madegowda
    'G Madegowda Institute of Technology': 103,
    # Rank 104 - GEC (Govt)
    'Government Engineering College': 104,
    'GOVERNMENT ENGINEERING COLLEGE': 104,
    # Rank 105 - DSU
    'Dayananda Sagar University': 105,
    # Rank 106 - Rao Bahadur
    'Rao Bahadur Y.Mahabaleswarappa': 106,
    # Rank 107 - Bangalore College of Eng
    'Bangalore College of Engineering': 107,
    # Rank 108 - Kalpatharu
    'Kalpatharu Institute of Technology': 108,
    # Rank 109 - RRIT / Rajiv Gandhi
    'Rajiv Gandhi Institute of Technology': 109,
    # Rank 110 - Jawaharlal Nehru
    'Jawaharlal Nehru New College': 110,
    # Rank 111 - Sri Sairam
    'Sri Sairam College of Engineering': 111,
    # Rank 112 - Secab
    'Secab Institute of Engineering': 112,
    # Rank 113 - Dr T Thimmaiah
    'Dr.T.Thimmaiah Institute of Technology': 113,
    # Rank 114 - Biluru Gurubasava
    'Biluru Gurubasava': 114,
    # Rank 115 - Shetty
    'Shetty Institute of Technology': 115,
    # Rank 116 - Channabasaveshwara
    'Channabasaveshwara Institute of Technology': 116,
    # Rank 117 - Ghousia
    'Ghousia': 117,
    # Rank 118 - Sampoorna
    'Sampoorna': 118,
    # Rank 119 - R.T.E. Rural
    "R.T.E. Soceity": 119,
    # Rank 120 - Sha-Shib
    'Sha-Shib College of Engineering': 120,
    # Rank 121 - C Byre Gowda
    'C Byre Gowda Institute of Technology': 121,
    # Rank 122 - Moodalakatte
    'Moodalakatte Institute of Technology': 122,
    # Rank 123 - Akshaya
    'Akshaya Institute of Technology': 123,
    # Rank 124 - Jain College Belagavi
    'Jain College of Engineering': 124,
    # Rank 125 - PDA College
    'P D A College of Engineering': 125,
    # Rank 126 - KLS Viswanathrao
    'K L S Viswanathrao Deshpande': 126,
    # Rank 127 - Vijaya Vittala
    'Vijaya Vittala Institute of Technology': 127,
    # Rank 128 - Sri Revana
    'Sri Revana Siddeswara': 128,
    # Rank 129 - Achutha
    'Achutha Institute of Technology': 129,
    # Rank 130 - Bangalore Technological
    'Bangalore Technological Institute': 130,
    # Rank 131 - ATME
    'ATME College of Engineering': 131,
    # Rank 132 - Yenepoya
    'Yenepoya Institute of Technology': 132,
    # Rank 133 - Girijabai
    'Girijabai Sail Institute of Technology': 133,
    # Rank 134 - Dr Shivakumara
    'Dr. Sri. Sri. Sri. Shivakumara': 134,
    # Rank 135 - Beary's
    "Beary": 135,
    # Rank 136 - AGM Rural
    'AGM Rural Engineering College': 136,
    # Rank 137 - Sharanbasava / Appa
    'Sharanbasava University': 137,
    'Sharnbasva University': 137,
    # Rank 138 - GITAM
    'GANDHI INSTITUTE OF TECHNOLOGY AND MANAGEMENT': 138,
    'Gandhi Institute of Technology': 138,
    'Gitam School Of Technology': 138,
    # Rank 139 - Alliance
    'ALLIANCE University': 139,
    'Alliance University': 139,
    # Rank 140 - Garden City
    'Garden City University': 140,
    # Rank 141 - AMITY
    'AMITY UNIVERSITY': 141,
    # Rank 142 - Presidency
    'PRESIDENCY University': 142,
    # Rank 143 - Vidyashilp
    'Vidyashilp University': 143,
    # Rank 144 - Chanakya
    'THE CHANAKYA UNIVERSITY': 144,
    # Rank 145 - GM University
    'G M UNIVERSITY': 145,
    'GM University': 145,
    # Rank 146 - Kishkinda
    'KISHKINDA UNIVERSITY': 146,
    # Rank 147 - MSRUAS
    'M.S. Ramaiah University of Applied Sciences': 147,
    'M . S . Ramaiah University of Applied Sciences': 147,
    # Rank 148 - Seshadripuram
    'SESHADRIPURAM INSTITUTE OF TECHNOLOGY': 148,
    # Rank 149 - Mysuru Royal
    'Mysuru Royal Institute': 149,
    # Rank 150 - Harsha
    'HARSHA INSTITUTE OF TECHNOLOGY': 150,
    # Rank 151 - Sapthagiri NPS
    'SAPTHAGIRI NPS': 151,
    # Rank 152 - BASAV Engineering
    'BASAV ENGINEERING SCHOOL': 152,
    # Rank 153 - DR HN National
    'DR H N NATIONAL': 153,
    # Rank 154 - SRI SIDDHARTHA SCHOOL
    'SRI SIDDHARTHA SCHOOL OF ENGINEERING': 154,
    # Rank 155 - Visvesvaraya TU
    'Visvesvaraya Technological University': 155,
    'VISVESVARAYA TECHNOLOGICAL UNIVERSITY': 155,
    # RV College of Architecture - separate institution
    'R V College of Architecture': 160,
    'R V University': 160,
    # Nitte School of Arch
    'Nitte School of Architecture': 165,
    # East West School of Arch
    'East West School of Architecture': 170,
    # Univ of Mysuru
    'University of Mysuru': 175,
}


def match_college(norm_name, manual_map):
    """Try to match a normalized college name against manual mapping using prefix matching."""
    # Exact match first
    if norm_name in manual_map:
        return manual_map[norm_name]
    
    # Prefix/substring match (longer matches preferred)
    best_rank = None
    best_len = 0
    for pattern, rank in manual_map.items():
        if pattern in norm_name or norm_name.startswith(pattern):
            if len(pattern) > best_len:
                best_len = len(pattern)
                best_rank = rank
    
    return best_rank


def main():
    # Load cutoff data and get all normalized college names
    cutoff_df = pd.read_csv(os.path.join(PROJECT_ROOT, 'data', 'clean_data', 'kcet_cutoffs_clean.csv'))
    cutoff_df['COLLEGE_NORM'] = cutoff_df['COLLEGE'].apply(normalize_college)
    norm_colleges = sorted(cutoff_df['COLLEGE_NORM'].unique())

    college_priority = {}
    unmatched = []

    for college in norm_colleges:
        rank = match_college(college, MANUAL_MAPPING)
        if rank is not None:
            college_priority[college] = rank
        else:
            unmatched.append(college)
            college_priority[college] = 999  # Default high rank for unmatched

    print(f"Matched: {len(norm_colleges) - len(unmatched)}/{len(norm_colleges)}")
    print(f"\nUnmatched ({len(unmatched)}) - assigned rank 999:")
    for c in unmatched:
        print(f"  - {c}")

    # Save the mapping as JSON
    output_path = os.path.join(PROJECT_DIR, 'college_priority.json')
    with open(output_path, 'w') as f:
        json.dump(college_priority, f, indent=2, ensure_ascii=False)

    print(f"\nSaved priority map to {output_path}")

    # Verify top-20
    print("\nTop 20 by priority:")
    sorted_cols = sorted(college_priority.items(), key=lambda x: x[1])
    for name, rank in sorted_cols[:25]:
        print(f"  {rank:3d}. {name}")


if __name__ == '__main__':
    main()
