import logging
import uuid
from datetime import datetime
from typing import Optional

from db import AsyncDRFClient, DRFClient
from fastapi import BackgroundTasks, Depends, FastAPI
from llm import LLM
from schemas import JobListingSchema, ScrapeRequest, TaskScheduleResponse
from scraper import (
    JustJoinITScraper,
    PracujplScraper,
    TheProtocolITScraper,
)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
logger.propagate = False
error_file_handler = logging.FileHandler("error_log.log")
error_file_handler.setLevel(logging.ERROR)
file_format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
error_file_handler.setFormatter(file_format)
logger.addHandler(error_file_handler)


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


def get_llm():
    return LLM("ollama")


def perform_scraping_task(
    llm: LLM,
    task_id: uuid.UUID,
    target_url: Optional[str] = None,
    target_portal: Optional[str] = None,
):
    logger.info("Task %s is EXECUTING now...", task_id)
    errors_occurred = False
    task_record = None
    drf = DRFClient()
    try:
        logger.info("Starting task...")
        task_record = _get_task_record(task_id)

        if target_url is not None and target_portal is not None:
            logger.info("Scraping single URL: %s from %s", target_url, target_portal)
            scraper = _get_scraper_for_portal(target_url, target_portal)
            try:
                _process_job_listing(llm, target_url, scraper)
            except Exception as e:
                logger.error("Error processing job listing %s: %s", target_url, e)
                errors_occurred = True
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
                if _scrape_portal(llm, scraper):
                    errors_occurred = True

        task_record["status"] = (
            "completed" if not errors_occurred else "completed_with_errors"
        )
        drf.post("tasks", task_record)
        drf.close()
        logger.info("Task %s completed.", task_id)
    except ValueError:
        pass
    except Exception as e:
        if task_record:
            task_record["status"] = "failed"
            drf.post("tasks", task_record)
            drf.close()
        else:
            logger.error(
                "Task %s failed before task_record could be created: %s", task_id, e
            )
        logger.error("Task %s failed: %s", task_id, e)


""" async def perform_matching_task(llm, task_id: uuid.UUID):
    logger.info("Matching Task %s is EXECUTING now...", task_id)
    errors_occurred = False
    task_record = None
    try:
        task_record = await sync_to_async(_get_task_record)(task_id)
        resume_pl = await sync_to_async(Resume.objects.get)(pk=1)
        resume_en = await sync_to_async(Resume.objects.get)(pk=2)

        def fetch_jobs():
            return list(JobListing.objects.all())

        all_jobs = await sync_to_async(fetch_jobs, thread_sensitive=False)()
        result = []
        for job in all_jobs:
            try:
                llm_output = llm.analyze_job_fit(
                    job, resume_pl.text_content, resume_en.text_content
                ).model_dump()
                await sync_to_async(JobMatch.objects.update_or_create)(
                    job_listing=job, llm_output=llm_output
                )
                result.append(llm_output)
            except Exception as e:
                logger.error("Error processing job match for job %s: %s", job.pk, e)
                errors_occurred = True
        task_record.status = (
            "completed" if not errors_occurred else "completed_with_errors"
        )
        await sync_to_async(task_record.save)()
        logger.info("Matching Task %s completed.", task_id)
    except ValueError:
        pass
    except Exception as e:
        if task_record:
            task_record.status = "failed"
            await sync_to_async(task_record.save)()
        else:
            logger.error(
                "Matching Task %s failed before task_record could be created: %s",
                task_id,
                e,
            )
        logger.error("Matching Task %s failed: %s", task_id, e) """


def _get_task_record(task_id: uuid.UUID) -> dict:
    drf = DRFClient()
    task_record = drf.get("tasks", f"task_id={task_id}")[0]
    if task_record.get("status") in ["in_progress", "completed"]:
        logger.debug("Task %s already handled. Skipping.", task_id)
        raise ValueError(f"Task {task_id} already handled.")
    task_record["status"] = "in_progress"
    drf.post("tasks", task_record)
    drf.close()
    return task_record


def _get_scraper_for_portal(url: str, portal: str):
    portal_map = {
        "JustJoinIT": JustJoinITScraper,
        "Pracuj.pl": PracujplScraper,
        "theprotocol.it": TheProtocolITScraper,
    }
    scraper_class = portal_map.get(portal)
    if scraper_class is None:
        raise ValueError(f"Unknown portal: {portal}")
    return scraper_class(url, portal)


def _process_job_listing(llm: LLM, job_listing_url: str, scraper) -> None:
    logger.debug("Scraping %s", job_listing_url)
    # portal = Portal.objects.get(name=scraper.portal)
    drf = DRFClient()
    portal = drf.get("portals", f"name={scraper.portal}")
    logger.debug(portal)
    text_content = scraper.get_data(job_listing_url, raw=True)
    payload = {
        "url": job_listing_url,
        "text_content": text_content,
        "portal": portal[0]["id"],
    }
    logger.debug("DEBUG: INITIAL POST PAYLOAD: %s", payload)
    obj = drf.post(
        "job_listings",
        payload,
    )
    logger.debug("Done with scraping. Starting LLM...")
    system_instruction = drf.get("system_instructions", "id=1")[0].get("instruction")
    prompts = f"### Context: today is {datetime.now().strftime('%A, %B %d, %Y')}.\n\n{system_instruction}"
    logger.debug("DEBUG: PROMPTS: %s", prompts)
    logger.debug("DEBUG: obj: %s", obj)
    listing_details = llm.get_listings_details(
        JobListingSchema.model_validate(obj), prompts
    )
    if isinstance(listing_details, JobListingSchema):
        listing_dict = listing_details.model_dump(mode="json")
        filtered_data = {k: v for k, v in listing_dict.items() if v is not None}
        obj.update(filtered_data)
        logger.debug("Listing dict before drf.post %s", obj)
        drf.post("job_listings", obj)
    drf.close()


def _scrape_portal(llm, scraper) -> bool:
    job_listings = scraper.get_all_listings()
    logger.info("%s items found for %s", len(job_listings), scraper)

    errors_occurred = False
    for index, job_listing in enumerate(job_listings):
        try:
            logger.info("%i. Processing job listing %s", index, job_listing)
            # logger.info("%i %s", index, job_listing)
            _process_job_listing(llm, job_listing, scraper)
        except Exception as e:
            logger.error(
                "Error processing job listing %i. %s: %s", index, job_listing, e
            )
            errors_occurred = True
    return errors_occurred


@app.get("/tasks/status/{task_id}", tags=["Scraping Tasks"])
async def get_task_status(task_id: uuid.UUID):
    drf = AsyncDRFClient()
    task = await drf.get("tasks", f"task_id={task_id}")
    await drf.close()
    return task


@app.post("/tasks/schedule-scraping")
async def schedule_scraping_task(
    background_tasks: BackgroundTasks,
    payload: Optional[ScrapeRequest] = None,
    llm: LLM = Depends(get_llm),
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
    drf = AsyncDRFClient()
    await drf.post("tasks", {"task_id": str(task_id), "status": "pending"})
    await drf.close()
    background_tasks.add_task(
        perform_scraping_task, llm, task_id, target_url, target_portal
    )
    logger.info("Job %s scheduled", task_id)
    return TaskScheduleResponse(
        task_id=str(task_id),
        message="Task started in background",
        status_url=f"/tasks/status/{task_id}",
    )


""" @app.post("/tasks/schedule-matching", response_model=TaskScheduleResponse)
async def schedule_matching_task(
    background_tasks: BackgroundTasks = BackgroundTasks(), llm: LLM = Depends(get_llm)
):
    task_id = uuid.uuid4()
    await sync_to_async(Task.objects.create)(task_id=task_id, status="pending")
    background_tasks.add_task(perform_matching_task, llm, task_id)
    logger.info("Matching Job %s scheduled", task_id)
    return TaskScheduleResponse(
        task_id=str(task_id),
        message="Matching task started in background",
        status_url=f"/tasks/status/{task_id}",
    ) """
