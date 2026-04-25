from datetime import date

import pytest
from pydantic import ValidationError
from schemas import (
    JobExtractionSchema,
    JobListingSchema,
    JobMatchAssessment,
    ScrapeRequest,
    TaskScheduleResponse,
)


class TestJobListingSchema:
    def test_all_fields_optional(self):
        schema = JobListingSchema()
        assert schema.title is None
        assert schema.company is None
        assert schema.text_content is None

    def test_valid_field_assignment(self):
        schema = JobListingSchema(
            title="Python Developer",
            company="TechCorp",
            text_content="Job description",
            portal=1,
            years_of_experience=3,
            salary="200000 PLN",
        )
        assert schema.title == "Python Developer"
        assert schema.company == "TechCorp"
        assert schema.portal == 1


class TestJobExtractionSchema:
    def test_valid_fields(self):
        schema = JobExtractionSchema(
            title="Senior Python",
            company="BigTech",
            years_of_experience=5,
            salary="300000 PLN",
        )
        assert schema.title == "Senior Python"
        assert schema.years_of_experience == 5

    def test_date_parsing_with_t_separator(self):
        schema = JobExtractionSchema(
            expiry_date="2026-12-25T10:30:00",
            posted_at="2026-04-01T08:00:00",
        )
        assert schema.expiry_date == date(2026, 12, 25)
        assert schema.posted_at == date(2026, 4, 1)

    def test_date_string_without_time(self):
        schema = JobExtractionSchema(expiry_date="2026-12-25")
        assert schema.expiry_date == date(2026, 12, 25)

    def test_invalid_date_string(self):
        with pytest.raises(ValidationError):
            JobExtractionSchema(expiry_date="not-a-date")
        # assert schema.expiry_date == "not-a-date"


class TestJobMatchAssessment:
    def test_valid_match_assessment(self):
        schema = JobMatchAssessment(
            match_percentage=85,
            experience_fit="Good fit",
            skill_alignment=["Python", "Django"],
            missing_criteria=["Kubernetes"],
            verdict="Apply",
        )
        assert schema.match_percentage == 85
        assert "Python" in schema.skill_alignment

    def test_match_percentage_boundary_0(self):
        schema = JobMatchAssessment(
            match_percentage=0,
            experience_fit="No fit",
            skill_alignment=[],
            missing_criteria=["Python"],
            verdict="Don't apply",
        )
        assert schema.match_percentage == 0

    def test_match_percentage_boundary_100(self):
        schema = JobMatchAssessment(
            match_percentage=100,
            experience_fit="Perfect fit",
            skill_alignment=["Python", "Django", "FastAPI"],
            missing_criteria=[],
            verdict="Apply immediately",
        )
        assert schema.match_percentage == 100

    def test_match_percentage_invalid_too_high(self):
        with pytest.raises(ValidationError):
            JobMatchAssessment(
                match_percentage=150,
                experience_fit="Fit",
                skill_alignment=[],
                missing_criteria=[],
                verdict="Fit",
            )

    def test_match_percentage_invalid_negative(self):
        with pytest.raises(ValidationError):
            JobMatchAssessment(
                match_percentage=-10,
                experience_fit="Fit",
                skill_alignment=[],
                missing_criteria=[],
                verdict="Fit",
            )


class TestTaskScheduleResponse:
    def test_valid_uuid_format(self):
        schema = TaskScheduleResponse(
            task_id="550e8400-e29b-41d4-a716-446655440000",
            message="Task started in background",
            status_url="/tasks/status/550e8400-e29b-41d4-a716-446655440000",
        )
        assert schema.task_id == "550e8400-e29b-41d4-a716-446655440000"

    def test_required_fields(self):
        with pytest.raises(ValidationError):
            TaskScheduleResponse(task_id="", message="", status_url="")


class TestScrapeRequest:
    def test_both_url_and_portal_provided(self):
        schema = ScrapeRequest(
            url="https://justjoin.it/job/python-dev",
            portal="JustJoinIT",
        )
        assert str(schema.url) == "https://justjoin.it/job/python-dev"
        assert schema.portal == "JustJoinIT"

    def test_neither_url_nor_portal_provided(self):
        schema = ScrapeRequest()
        assert schema.url is None
        assert schema.portal is None

    def test_only_url_raises_error(self):
        with pytest.raises(ValidationError) as exc_info:
            ScrapeRequest(url="https://justjoin.it/job/python-dev")
        assert "both 'url' and 'portal'" in str(exc_info.value)

    def test_only_portal_raises_error(self):
        with pytest.raises(ValidationError) as exc_info:
            ScrapeRequest(portal="JustJoinIT")
        assert "both 'url' and 'portal'" in str(exc_info.value)

    def test_different_portal_names(self):
        portals = ["JustJoinIT", "Pracuj.pl", "theprotocol.it"]
        for portal in portals:
            schema = ScrapeRequest(
                url="https://example.com/job",
                portal=portal,
            )
            assert schema.portal == portal
