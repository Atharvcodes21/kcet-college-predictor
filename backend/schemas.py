from pydantic import BaseModel, Field

class PredictionRequest(BaseModel):
    rank: int = Field(..., description="Student's KCET Rank", gt=0)
    category: str = Field(..., description="Reservation Category (e.g., GM, 2A, 3B, Cat-1, SC, ST)")
    courses: list[str] = Field(..., description="List of preferred course branches")
    is_hk_region: bool = Field(False, description="Hyderabad-Karnataka (371J) region status")
    is_rural: bool = Field(False, description="Rural Quota status")
    is_kannada: bool = Field(False, description="Kannada Medium Quota status")

class CollegeResult(BaseModel):
    college: str
    course: str
    cutoff: int
    year: int
    can_get: bool       # True if student rank <= cutoff rank
    margin: int         # cutoff - rank (positive = safe, negative = out of reach)
    priority_rank: int = 999   # College priority rank from Excel (1 = best)
    tier: str = ""             # Tier label (e.g., "Tier 1: Elite & Highly Competitive")
    qualifying_pool: str = ""  # The actual pool the student qualifies under (e.g. "3B (Rural)", "GM (Rural)")
    college_full: str = ""     # Complete college name as in PDF
    cet_code: str = ""         # CET code of the college (e.g. E001)

class MetadataResponse(BaseModel):
    courses: list[str]
    categories: list[str]
    total_colleges: int
    data_year: int
