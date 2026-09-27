# 🎓 KCET Smart Option Entry Predictor

A data-driven web application designed to help Karnataka students navigate the complexities of the KCET counseling process. By analyzing five years of historical cutoff data, the system predicts the probability of seat allotment across various categories, branches, and the Hyderabad-Karnataka (371J) region.

## 🚀 The Problem Statement
The KCET counseling process involves a complex matrix of categories (e.g., GM, 2A, 3B), sub-quotas (Rural, Kannada Medium), and regional reservations that shift annually. Students frequently make suboptimal Option Entry choices due to a lack of probabilistic data. This project replaces guesswork with a deterministic Machine Learning approach.

## 🏗️ System Architecture

### 1. Frontend Interface (UI/UX)
*   **Tech Stack:** HTML5, CSS3, Vanilla JavaScript.
*   **Design Pattern:** Implements an "Anti-Gravity" CSS physics animation for result cards to provide a modern, highly interactive user experience.
*   **API Integration:** Utilizes the `Fetch API` for asynchronous JSON payload transmission.

### 2. Backend Engine (API)
*   **Tech Stack:** FastAPI (Python).
*   **Role:** Serves as the high-speed inference bridge. Validates incoming constraints using `Pydantic` and passes the sanitized data to the compiled Machine Learning model.
*   **Deployment:** Optimized for lightweight, stateless deployment on free-tier cloud platforms.

### 3. Predictive Modeling (Machine Learning)
*   **Core Algorithm:** Extreme Gradient Boosting (XGBoost).
*   **Algorithmic Advantage:** Selected over K-Nearest Neighbors (KNN) due to its sub-millisecond inference time, native handling of highly dimensional categorical matrices, and ability to model the non-linear relationship between student ranks and cutoff probabilities.

---

## ⚙️ Data Engineering: The "Forward-Fill" Anomaly

The most significant bottleneck in processing Karnataka Examinations Authority (KEA) PDFs is their unstructured tabular format. Specifically, **college names are often printed as standalone subheadings** rather than standard column variables, which breaks standard PDF parsing libraries.

### The Solution: `ffill` Algorithm
To resolve this, the data pipeline implements a Forward-Fill (`ffill`) state manipulation algorithm using Pandas. The script identifies the subheading trigger, extracts the college name into a new column, and mathematically drags it downward to associate it with the corresponding courses.

**Core Extraction Logic:**
```python
# 1. Initialize an empty column for the College Name
df['COLLEGE'] = np.nan

# 2. Identify rows acting as subheadings and extract the text
college_mask = df['COURSE NAME'].str.contains('COLLEGE:', na=False, case=False)
df.loc[college_mask, 'COLLEGE'] = df.loc[college_mask, 'COURSE NAME']

# 3. Forward-Fill (Drag the college name down to the course rows)
df['COLLEGE'] = df['COLLEGE'].ffill()

# 4. Drop the original subheading rows to clean the matrix
df = df[~college_mask].dropna(subset=['COURSE NAME'])

Regional Quota Tagging
The pipeline also normalizes KEA's category syntax (e.g., swapping G for H in GMH vs GM) by appending a Quota_Region column during the batch processing phase, ensuring the ML model can mathematically differentiate between standard seats and Article 371(J) seats.

🛠️ Local Installation & Setup
Clone the Repository:

Bash
git clone [https://github.com/yourusername/kcet-predictor.git](https://github.com/yourusername/kcet-predictor.git)
cd kcet-predictor
Install Python Dependencies:

Bash
pip install -r backend/requirements.txt
Execute the Data Pipeline:
Ensure your KEA PDFs are placed in data/raw_pdfs/ prior to execution.

Bash
python ml_pipeline/data_pipeline.py
Initialize the Local Server:

Bash
uvicorn backend.app:app --reload
🗺️ Project Roadmap
[x] Establish Data Architecture and Directory State

[x] 5-Year KEA PDF Data Extraction

[x] Forward-Fill (ffill) College Name Mapping

[x] Kalyana-Karnataka (371J) Quota Logic Integration

[x] Train and Export XGBoost Baseline Model (Phase 2)

[x] Develop FastAPI REST Endpoints (Phase 3)

[ ] Live Deployment (Phase 5)

Disclaimer: This application is engineered strictly for educational and probabilistic analysis. Final seat allotments remain solely under the jurisdiction of the Karnataka Examinations Authority (KEA).


***

With the data extraction logic perfected and the documentation finalized, the messy data engineering phase is effectively complete. Are you ready to move into the `ml_pipeline` folder and begin writing the script to train the actual predictive model?