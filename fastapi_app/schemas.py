from datetime import date, datetime
from typing import List, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)


class JobListingSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    # Fields
    title: Optional[str] = Field(default=None, max_length=100)
    company: Optional[str] = Field(default=None, max_length=100)
    text_content: Optional[str] = None
    portal: Optional[int] = None
    expiry_date: Optional[date] = None
    url: Optional[HttpUrl] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    years_of_experience: Optional[int] = None
    salary: Optional[str] = None
    posted_at: Optional[date] = None


class JobExtractionSchema(BaseModel):
    title: Optional[str] = Field(default=None, max_length=100)
    company: Optional[str] = Field(default=None, max_length=100)
    years_of_experience: Optional[int] = None
    salary: Optional[str] = None
    expiry_date: Optional[date] = None
    posted_at: Optional[date] = None

    @field_validator("expiry_date", "posted_at", mode="before")
    @classmethod
    def parse_iso_date(cls, v):
        if isinstance(v, str) and v:
            # Splits "2026-04-17T09:21..." at the 'T' and takes the first part
            return v.split("T")[0]
        return v


class JobMatchAssessment(BaseModel):
    match_percentage: int = Field(..., ge=0, le=100)
    experience_fit: str
    skill_alignment: List[str]
    missing_criteria: List[str]
    verdict: str


class TaskScheduleResponse(BaseModel):
    task_id: str = Field(
        ..., min_length=1, examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    message: str = Field(..., min_length=1, examples=["Task started in background"])
    status_url: str = Field(
        ...,
        min_length=1,
        examples=["/tasks/status/550e8400-e29b-41d4-a716-446655440000"],
    )


class ScrapeRequest(BaseModel):
    url: Optional[HttpUrl] = Field(
        default=None,
        description="The specific job listing URL. **If provided, 'portal' must also be provided.**",
        examples=["https://theprotocol.it/filtry/python;t/backend;sp"],
    )
    portal: Optional[str] = Field(
        default=None,
        description="The name of the portal (e.g., 'JustJoinIT'). **Required if 'url' is provided.**",
        examples=["theprotocol.it"],
    )

    @model_validator(mode="after")
    def check_both_or_none(self) -> "ScrapeRequest":
        # Check if one is present but the other isn't
        if bool(self.url) != bool(self.portal):
            raise ValueError(
                "You must provide both 'url' and 'portal', or leave both empty."
            )
        return self
