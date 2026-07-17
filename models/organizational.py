from dataclasses import dataclass
from typing import Optional

@dataclass
class Organization:
    id: Optional[int]
    name: str
    registration_number: Optional[str] = None
    country: Optional[str] = None
    verified: bool = False

@dataclass
class Report:
    id: Optional[int]
    org_id: int
    uploaded_by: int
    file_path: str
    extracted_text: str = ""

@dataclass
class Score:
    id: Optional[int]
    report_id: int
    admin_cost_percentage: float
    transparency_score: int
    red_flags: str
    ai_summary: str