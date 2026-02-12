import os
import uuid

import django
from asgiref.sync import sync_to_async
from fastapi import BackgroundTasks, FastAPI
from scraper import JobScraper

# 1. Setup the environment variable
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "job_finder.settings")

# 2. Initialize Django (Must happen BEFORE importing models)
django.setup()

# 3. Now you can safely import from your Django app

app = FastAPI()
from tasks.models import Task  # type: ignore # noqa: E402

""" @app.get("/portals")
async def get_all_portals():
    # We wrap the logic of fetching 'all' and converting to a 'list'
    get_all_sync = sync_to_async(lambda: list(Portal.objects.all()))

    portals = await get_all_sync()

    # Return as a list of dictionaries
    result = [{"id": p.id, "name": p.name, "url": p.url} for p in portals]
    print(result)
    return result """


def perform_scraping_task(task_id: str):
    print(f"DEBUG: Task {task_id} is EXECUTING now...")
    # This runs AFTER the response is sent
    try:
        print("Starting task...")
        task_record = Task.objects.get(task_id=task_id)
        task_record.status = "in_progress"
        task_record.save()
        task = JobScraper("https://it.pracuj.pl/praca?sc=0&its=backend&itth=37")
        data = task.get_data()
        task_record.status = "completed"
        task_record.save()
        print(f"Task {task_id} completed successfully.")
    except Exception as e:
        print(f"Task {task_id} failed: {e}")


@app.post("/tasks/schedule")
async def schedule_task(background_tasks: BackgroundTasks):
    task_id = uuid.uuid4()
    await sync_to_async(Task.objects.create)(task_id=task_id, status="pending")
    background_tasks.add_task(perform_scraping_task, task_id)
    print(f"Job {task_id}")
    return {"task_id": str(task_id), "message": "Task started in background"}
