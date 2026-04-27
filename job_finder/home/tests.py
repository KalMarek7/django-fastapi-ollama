import pytest
from django.http import HttpResponse

from home.admin import export_as_csv, replace_api_url
from home.models import JobListing, JobMatch, Portal, Resume, SystemInstruction


@pytest.mark.django_db
class TestPortalModel:
    def test_portal_creation(self):
        portal = Portal.objects.create(name="TestPortal", url="https://testportal.com")
        assert portal.name == "TestPortal"
        assert portal.url == "https://testportal.com"
        assert portal.is_active is True

    def test_portal_str_representation(self):
        portal = Portal.objects.create(name="JustJoinIT", url="https://justjoin.it")
        assert str(portal) == "JustJoinIT"

    """
    def test_portal_allows_duplicate_names(self):
        Portal.objects.create(name="DupPortal", url="https://a.com")
        portal2 = Portal.objects.create(name="DupPortal", url="https://b.com")
        assert Portal.objects.filter(name="DupPortal").count() == 1
    """


@pytest.mark.django_db
class TestSystemInstructionModel:
    def test_system_instruction_creation(self):
        instruction = SystemInstruction.objects.create(
            name="Extract Job Details",
            instruction="Extract title, company, salary from job posting.",
            description="Testing",
        )
        assert instruction.name == "Extract Job Details"
        assert (
            instruction.instruction
            == "Extract title, company, salary from job posting."
        )

    def test_system_instruction_str(self):
        instruction = SystemInstruction.objects.create(
            name="TestInstr", instruction="test"
        )
        assert str(instruction) == "TestInstr"


@pytest.mark.django_db
class TestJobListingModel:
    def setup_method(self):
        self.portal = Portal.objects.create(name="TestPortal", url="https://test.com")

    def test_job_listing_creation(self):
        job = JobListing.objects.create(
            title="Python Developer",
            company="TechCorp",
            text_content="We are looking for a Python developer...",
            url="https://test.com/job/1",
            portal=self.portal,
        )
        assert job.title == "Python Developer"
        assert job.company == "TechCorp"
        assert job.portal == self.portal

    def test_job_listing_with_optional_fields(self):
        job = JobListing.objects.create(
            title="Senior Python Dev",
            company="BigTech",
            text_content="Python role...",
            url="https://test.com/job/2",
            portal=self.portal,
            years_of_experience=5,
            salary="200000-300000 PLN",
        )
        assert job.years_of_experience == 5
        assert job.salary == "200000-300000 PLN"

    def test_job_listing_unique_url(self):
        JobListing.objects.create(
            title="Job 1",
            text_content="content",
            url="https://test.com/job/unique",
            portal=self.portal,
        )
        with pytest.raises(Exception):
            JobListing.objects.create(
                title="Job 2",
                text_content="content",
                url="https://test.com/job/unique",
                portal=self.portal,
            )


@pytest.mark.django_db
class TestResumeModel:
    def test_resume_creation(self):
        resume = Resume.objects.create(
            name="My Resume", text_content="Experienced Python developer..."
        )
        assert resume.name == "My Resume"
        assert resume.text_content == "Experienced Python developer..."

    def test_resume_str(self):
        resume = Resume.objects.create(name="CV 2024", text_content="content")
        assert str(resume) == "CV 2024"


@pytest.mark.django_db
class TestJobMatchModel:
    def setup_method(self):
        self.portal = Portal.objects.create(name="TestPortal", url="https://test.com")
        self.job = JobListing.objects.create(
            title="Python Dev",
            text_content="Looking for python dev",
            url="https://test.com/job/1",
            portal=self.portal,
        )

    def test_job_match_creation(self):
        match = JobMatch.objects.create(
            job_listing=self.job,
            llm_output={"match_percentage": 85, "verdict": "Apply"},
        )
        assert match.job_listing == self.job
        assert match.llm_output["match_percentage"] == 85

    def test_job_match_unique_constraint(self):
        JobMatch.objects.create(
            job_listing=self.job, llm_output={"match_percentage": 75}
        )
        with pytest.raises(Exception):
            JobMatch.objects.create(
                job_listing=self.job, llm_output={"match_percentage": 90}
            )


@pytest.mark.django_db
class TestAdminActions:
    def setup_method(self):
        self.portal = Portal.objects.create(
            name="JustJoinIT", url="https://justjoin.it"
        )
        self.other_portal = Portal.objects.create(name="Other", url="https://other.com")

    def _create_mock_request(self):
        class MockRequest:
            pass

        return MockRequest()

    def _create_mock_modeladmin(self, list_display):
        class MockModelAdmin:
            def __init__(self, list_display):
                self.list_display = list_display

            def message_user(self, request, message, level=None):
                self.last_message = message
                self.last_level = level

        return MockModelAdmin(list_display)

    def test_export_as_csv_creates_csv_response(self):
        JobListing.objects.create(
            title="Python Dev",
            company="TechCorp",
            text_content="job desc",
            url="https://justjoin.it/job/1",
            portal=self.portal,
        )

        request = self._create_mock_request()
        modeladmin = self._create_mock_modeladmin(["title", "company"])
        queryset = JobListing.objects.all()

        result = export_as_csv(modeladmin, request, queryset)

        assert isinstance(result, HttpResponse)
        assert result["Content-Type"] == "text/csv"
        assert "attachment" in result["Content-Disposition"]

    def test_replace_api_url_updates_justjoinit_urls(self):
        JobListing.objects.create(
            title="Job 1",
            company="Company",
            text_content="desc",
            url="https://justjoin.it/api/candidate-api/offers/test-job-1",
            portal=self.portal,
        )

        request = self._create_mock_request()
        modeladmin = self._create_mock_modeladmin(["title"])
        queryset = JobListing.objects.all()

        replace_api_url(modeladmin, request, queryset)

        job = JobListing.objects.first()
        assert job is not None
        assert job.url is not None
        assert "/job-offer" in job.url
        assert "/api/candidate-api/offers" not in job.url

    def test_replace_api_url_no_justjoinit_returns_warning(self):
        JobListing.objects.create(
            title="Job 2",
            company="Company",
            text_content="desc",
            url="https://other.com/job/1",
            portal=self.other_portal,
        )

        request = self._create_mock_request()
        modeladmin = self._create_mock_modeladmin(["title"])
        queryset = JobListing.objects.all()

        result = replace_api_url(modeladmin, request, queryset)

        assert result is None
        assert hasattr(modeladmin, "last_message")
        assert "No JustJoinIT listings" in modeladmin.last_message
