from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl


class JobListingSchema(BaseModel):
    title: Optional[str] = Field(None, max_length=100)
    company: Optional[str] = Field(None, max_length=100)
    text_content: Optional[str] = None
    portal_id: Optional[int] = None
    expiry_date: Optional[date] = None
    url: Optional[HttpUrl] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    years_of_experience: Optional[int] = None
    salary: Optional[str] = None
    posted_at: Optional[date] = None

    class Config:
        from_attributes = True


class JobExtractionSchema(BaseModel):
    title: Optional[str]
    company: Optional[str]
    salary: Optional[str]
    years_of_experience: Optional[int]
    posted_at: Optional[date]
    expiry_date: Optional[date]


class JobMatchAssessment(BaseModel):
    match_percentage: int = Field(..., ge=0, le=100)
    experience_fit: str
    skill_alignment: List[str]
    missing_criteria: List[str]
    verdict: str
