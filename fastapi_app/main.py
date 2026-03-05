import logging
import os
import uuid
from typing import Optional

import django
from asgiref.sync import sync_to_async
from fastapi import BackgroundTasks, FastAPI
from pydantic import BaseModel, Field, HttpUrl, model_validator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)
from scraper import (  # noqa: E402, F401
    JobListingSchema,
    JustJoinITScraper,
    PracujplScraper,
    TheProtocolITScraper,
    get_listings_details,
)

# 1. Setup the environment variable
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "job_finder.settings")

# 2. Initialize Django (Must happen BEFORE importing models)
django.setup()

# 3. Now you can safely import from your Django app

app = FastAPI(
    title="Job Scraper Engine",
    description="LLM-powered job extraction service using Gemma & Django.",
    version="1.0.0",
    openapi_tags=[
        {
            "name": "Scraping Tasks",
            "description": "Endpoints for managing background scraping jobs.",
        }
    ],
)
from home.models import (  # type: ignore # noqa: E402
    JobListing,
    Portal,
    SystemInstruction,
)
from tasks.models import Task  # type: ignore # noqa: E402


# Use a response model for the UI to show the output structure
class TaskScheduleResponse(BaseModel):
    task_id: str = Field(..., examples=["550e8400-e29b-41d4-a716-446655440000"])
    message: str = Field(..., examples=["Task started in background"])
    status_url: str = Field(
        ..., examples=["/tasks/status/550e8400-e29b-41d4-a716-446655440000"]
    )


def _get_task_record(task_id: uuid.UUID) -> Task:
    task_record = Task.objects.get(task_id=task_id)
    if task_record.status in ["in_progress", "completed"]:
        logger.debug("Task %s already handled. Skipping.", task_id)
        raise ValueError(f"Task {task_id} already handled.")
    task_record.status = "in_progress"
    task_record.save()
    return task_record


def _process_job_listing(job_listing_url: str, scraper) -> None:
    logger.debug("Scraping %s", job_listing_url)
    portal = Portal.objects.get(name=scraper.portal)
    text_content = scraper.get_data(job_listing_url, raw=True)

    obj, created = JobListing.objects.update_or_create(
        url=job_listing_url,
        defaults={
            "text_content": text_content,
            "portal": portal,
        },
    )
    logger.debug("Done with scraping. Starting LLM...")

    jls = get_listings_details(
        JobListingSchema.model_validate(obj),
        SystemInstruction.objects.get(pk=1).instruction,
    )
    if isinstance(jls, JobListingSchema):
        JobListing.objects.filter(url=job_listing_url).update(
            title=jls.title,
            expiry_date=jls.expiry_date,
            company=jls.company,
        )


def _scrape_portal(scraper) -> None:
    job_listings = scraper.get_all_listings()
    logger.info("%s items found for %s", len(job_listings), scraper)

    for job_listing in job_listings[10:15]:
        _process_job_listing(job_listing, scraper)


def _get_scraper_for_portal(url: str, portal: str):
    portal_map = {
        "Pracuj.pl": PracujplScraper,
        "JustJoinIT": JustJoinITScraper,
        "theprotocol.it": TheProtocolITScraper,
    }
    scraper_class = portal_map.get(portal)
    if scraper_class is None:
        raise ValueError(f"Unknown portal: {portal}")
    return scraper_class(url, portal)


def perform_scraping_task(
    task_id: uuid.UUID,
    target_url: Optional[str] = None,
    target_portal: Optional[str] = None,
):
    logger.info("Task %s is EXECUTING now...", task_id)
    try:
        logger.info("Starting task...")
        task_record = _get_task_record(task_id)

        if target_url is not None and target_portal is not None:
            logger.info("Scraping single URL: %s from %s", target_url, target_portal)
            scraper = _get_scraper_for_portal(target_url, target_portal)
            _process_job_listing(target_url, scraper)
        else:
            scrapers = [
                PracujplScraper(
                    "https://it.pracuj.pl/praca?sc=0&its=backend&itth=37", "Pracuj.pl"
                ),
                JustJoinITScraper(
                    "https://justjoin.it/api/candidate-api/offers?from=0&itemsCount=100&categories=python&currency=pln&orderBy=descending&sortBy=publishedAt",
                    "JustJoinIT",
                ),
                TheProtocolITScraper(
                    "https://theprotocol.it/filtry/python;t/backend;sp",
                    "theprotocol.it",
                ),
            ]

            for scraper in scrapers:
                _scrape_portal(scraper)

        task_record.status = "completed"
        task_record.save()
        logger.info("Task %s completed successfully.", task_id)
    except ValueError:
        pass
    except Exception as e:
        try:
            task_record.status = "failed"
            task_record.save()
        except UnboundLocalError:
            logger.error(
                "Task %s failed before task_record could be created: %s", task_id, e
            )
        logger.error("Task %s failed: %s", task_id, e)


class ScrapeRequest(BaseModel):
    url: Optional[HttpUrl] = Field(
        None,
        description="The specific job listing URL. **If provided, 'portal' must also be provided.**",
        examples=["https://theprotocol.it/filtry/python;t/backend;sp"],
    )
    portal: Optional[str] = Field(
        None,
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


@app.post("/tasks/schedule")
async def schedule_task(
    payload: Optional[ScrapeRequest] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """
    This endpoint:
    1. Generates a unique **UUID**.
    2. Persists a **pending** task in the Django database.
    3. Offloads the heavy scraping/LLM logic to a **Background Task**.

    Send empty payload `{}` to scrape all jobs from all portals.
    Send payload with `url` and `portal` to scrape a specific job from a specific portal.
    """
    task_id = uuid.uuid4()
    # Defaults for global scrape
    target_url = None
    target_portal = None

    if payload is not None and payload.url is not None:
        target_url = str(payload.url)
        target_portal = payload.portal
        logger.info(
            "Task %s is scheduled for %s on %s", task_id, target_url, target_portal
        )
    await sync_to_async(Task.objects.create)(task_id=task_id, status="pending")
    background_tasks.add_task(perform_scraping_task, task_id, target_url, target_portal)
    logger.info("Job %s scheduled", task_id)
    return {
        "task_id": str(task_id),
        "message": "Task started in background",
        "status_url": f"/tasks/status/{task_id}",
    }


@app.get("/tasks/status/{task_id}", tags=["Scraping Tasks"])
async def get_task_status(task_id: uuid.UUID):
    task = await sync_to_async(Task.objects.get)(task_id=task_id)
    return {
        "task_id": task.task_id,
        "status": task.status,
        "updated_at": task.updated_at,
    }
