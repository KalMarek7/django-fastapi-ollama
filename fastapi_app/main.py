import os
import uuid
from typing import Optional

import django
from asgiref.sync import sync_to_async
from fastapi import BackgroundTasks, FastAPI
from pydantic import BaseModel, Field, HttpUrl, model_validator
from scraper import (  # noqa: F401
    JobListingSchema,
    JustJoinITScraper,
    NoFluffJobsScraper,
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
from home.models import JobListing, Portal  # type: ignore # noqa: E402
from tasks.models import Task  # type: ignore # noqa: E402


# Use a response model for the UI to show the output structure
class TaskScheduleResponse(BaseModel):
    task_id: str = Field(..., examples=["550e8400-e29b-41d4-a716-446655440000"])
    message: str = Field(..., examples=["Task started in background"])
    status_url: str = Field(
        ..., examples=["/tasks/status/550e8400-e29b-41d4-a716-446655440000"]
    )


def perform_scraping_task(task_id: uuid.UUID):
    print(f"DEBUG: Task {task_id} is EXECUTING now...")
    # This runs AFTER the response is sent
    try:
        print("Starting task...")
        task_record = Task.objects.get(task_id=task_id)
        if task_record.status in ["in_progress", "completed"]:
            print(f"DEBUG: Task {task_id} already handled. Skipping.")
            return
        task_record.status = "in_progress"
        task_record.save()
        """
        tasks = [
        
        task_nfj = NoFluffJobsScraper(
        "https://nofluffjobs.com/api/search/posting?sort=newest&withSalaryMatch=true&pageTo=2&pageSize=20&salaryCurrency=PLN&
        salaryPeriod=month&region=pl&language=pl-PL"
        ) 
        ]
        
        """
        task_tp = TheProtocolITScraper(
            "https://theprotocol.it/filtry/python;t/backend;sp", "theprotocol.it"
        )
        task_jjit = JustJoinITScraper(
            "https://justjoin.it/api/candidate-api/offers?from=0&itemsCount=100&categories=python&currency=pln&orderBy=descending&sortBy=publishedAt",
            "JustJoinIT",
        )
        task_pracuj = PracujplScraper(
            "https://it.pracuj.pl/praca?sc=0&its=backend&itth=37", "Pracuj.pl"
        )
        for task in [task_pracuj, task_jjit, task_tp]:
            job_listings = task.get_all_listings()
            print(f"DEBUG: {len(job_listings)} items found for {task}")
            result = []
            for job_listing in job_listings[:10]:
                print(f"DEBUG: Scraping {job_listing}")
                obj, created = JobListing.objects.update_or_create(
                    url=job_listing,
                    defaults={
                        "text_content": task.get_data(job_listing, raw=True),
                        "portal": Portal.objects.get(name=task.portal),
                    },
                )
                print("DEBUG: Done with scraping. Starting LLM...")
                # 4. Get LLM results
                jls = get_listings_details(JobListingSchema.model_validate(obj))
                JobListing.objects.filter(url=job_listing).update(
                    title=jls.title,
                    expiry_date=jls.expiry_date,  #  # type: ignore
                    company=jls.company,  # type: ignore
                )
        task_record.status = "completed"
        task_record.save()
        print(f"Task {task_id} completed successfully.")
        return result
    except Exception as e:
        task_record.status = "failed"
        task_record.save()
        print(f"Task {task_id} failed: {e}")


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

    Send empty payload to scrape all jobs from all portals.
    Send payload with `url` and `portal` to scrape a specific job from a specific portal.
    """
    task_id = uuid.uuid4()
    # Defaults for global scrape
    target_url = None
    target_portal = None

    if payload and payload.url:
        target_url = str(payload.url)
        target_portal = payload.portal
        print(f"DEBUG: Task {task_id} is scheduled for {target_url} on {target_portal}")
    await sync_to_async(Task.objects.create)(task_id=task_id, status="pending")
    background_tasks.add_task(perform_scraping_task, task_id)
    print(f"Job {task_id}")
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
