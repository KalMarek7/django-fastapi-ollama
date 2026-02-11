import os
import uuid

import django
from fastapi import BackgroundTasks, FastAPI

# 1. Setup the environment variable
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "job_finder.settings")

# 2. Initialize Django (Must happen BEFORE importing models)
django.setup()

# 3. Now you can safely import from your Django app

app = FastAPI()


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
        print(f"Task {task_id} completed successfully.")
    except Exception as e:
        print(f"Task {task_id} failed: {e}")


@app.post("/jobs/schedule")
async def schedule_job(background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    background_tasks.add_task(perform_scraping_task, task_id)
    return {"task_id": task_id, "message": "Job started in background"}
