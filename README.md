# Job Scraper Engine | AI-Powered IT Job Aggregator

A production-ready backend application that scrapes job listings from major Polish IT portals, leverages local LLMs (Ollama) for intelligent job data extraction, and exposes everything through a robust REST API. Built with Django, FastAPI, and PostgreSQL.

## Purpose

This project started as a way to automate my job search across multiple Polish IT portals. It evolved into a learning exercise to understand how the pieces fit together in a real-world Python application:

- **Django** + **DRF** — Built a Django backend with Django Rest Framework API for data storage and retrieval
- **FastAPI** — Added async background task handling for long-running scraping jobs
- **Ollama** — Integrated a local LLM to parse unstructured HTML into structured data
- **BeautifulSoup4** — Scraped multiple job portals with rate limiting and retry logic
- **Docker Compose** — Tied everything together with Docker
- **PostgreSQL** — Learned Django ORM patterns, migrations, relationships
- **Prompt engineering** — Experimented with getting structured output from freeform text

The goal was to have a working automation tool while learning each technology hands-on, rather than building a toy project.

## Key Features

- **Multi-Portal Scraping** - Aggregates jobs from Pracuj.pl, JustJoinIT, and TheProtocol.it
- **LLM-Powered Extraction** - Uses Llama 3.2 (via Ollama) to parse raw HTML into structured job data (title, company, salary, experience level)
- **Background Task Processing** - Async job scheduling with FastAPI background tasks
- **RESTful API** - Full CRUD operations via Django REST Framework
- **Persistent Storage** - PostgreSQL database with Django ORM
- **Dockerized** - One-command deployment with Docker Compose

## Technical Stack

| Layer | Technology |
|-------|------------|
| **Backend Framework** | Django, Django REST Framework, FastAPI |
| **Database** | PostgreSQL |
| **LLM** | Ollama (Llama 3.2) |
| **Scraping** | BeautifulSoup4, httpx |
| **Data Validation** | Pydantic |
| **Containerization** | Docker, Docker Compose |
| **Python** | 3.12 |

## Architecture Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Django DRF    │────▶│   PostgreSQL     │◀────│   FastAPI       │
│   (Port 8000)   │     │   (Port 5432)    │     │   (Port 8001)   │
└────────┬────────┘     └──────────────────┘     └────────┬────────┘
         │                                                │
         │              ┌──────────────────┐              │
         └─────────────▶│     Ollama       │◀─────────────┘
                        │  (LLM Engine)    │
                        │  (Port 11434)   │
                        └──────────────────┘
```

**Data Flow:**

1. FastAPI receives a scraping request via `/tasks/schedule-scraping`
2. Background task scrapes portals (Pracuj.pl, JustJoinIT, TheProtocol.it)
3. Raw HTML is cleaned and stored in PostgreSQL via Django REST API
4. Ollama (Llama 3.2) extracts structured fields from raw text
5. Django REST Framework serves the processed data to frontend clients

## Quick Start

### Prerequisites

- Docker & Docker Compose
- 8GB+ RAM (for Ollama with Llama 3.2)
- Git

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/KalMarek7/django-fastapi-ollama.git
cd django-fastapi-ollama
```

2. **Configure environment variables**

```bash
cp .env.example .env
# Edit .env with your database credentials
```

3. **Start all services**

```bash
docker compose up
```

4. **Verify services are running**

| Service | URL | Description |
|---------|-----|-------------|
| Django | http://localhost:8000/admin | Site administration |
| FastAPI | http://localhost:8001/docs | Scraping engine endpoints |
| Ollama | http://localhost:11434 | LLM inference |

5. **Pull the LLM model (first time only)**

```bash
docker compose exec -it ollama ollama pull llama3.2
```

6. **Run Django migrations**

```bash
docker compose exec django python manage.py migrate
```

## API Usage

### Schedule a Full Scraping Job

Scrapes all Python jobs from all configured portals:

```bash
curl -X POST http://localhost:8001/tasks/schedule-scraping \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Response:**

```json
{
  "task_id": "uuid-string-here",
  "message": "Task started in background",
  "status_url": "/tasks/status/uuid-string-here"
}
```

### Scrape a Specific Job Listing

```bash
curl -X POST http://localhost:8001/tasks/schedule-scraping \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://justjoin.it/api/candidate-api/offers/job-slug",
    "portal": "JustJoinIT"
  }'
```

### Check Task Status

```bash
curl http://localhost:8001/tasks/status/{task_id}
```

### Get All Job Listings (Django API)

```bash
curl http://localhost:8000/api/job-listings/
```

### Filter Jobs

```bash
# By company
curl "http://localhost:8000/api/job-listings/?company=Google"

# By portal
curl "http://localhost:8000/api/job-listings/?portal=JustJoinIT"
```

## LLM Implementation Details

### Prompt Engineering

The system uses a two-stage prompting approach:

1. **System Instruction** - Configurable prompt stored in database that defines extraction rules
2. **Dynamic Context** - Today's date is injected to help LLM assess job freshness

### Structured Output

Pydantic schemas enforce strict validation:

```python
class JobExtractionSchema(BaseModel):
    title: Optional[str] = Field(default=None, max_length=100)
    company: Optional[str] = Field(default=None, max_length=100)
    years_of_experience: Optional[int] = None
    salary: Optional[str] = None
    expiry_date: Optional[date] = None
    posted_at: Optional[date] = None
```

### Retry Logic

Tenacity handles transient failures with exponential backoff:

- 5 retry attempts
- 3-second wait between retries
- Automatic retry on HTTP errors and connection timeouts

## Project Structure

```
django-fastapi-cv/
├── docker-compose.yml          # Orchestration
├── .env                        # Environment config
├── job_finder/                 # Django application
│   ├── requirements.txt
│   ├── manage.py
│   ├── home/                   # Models (JobListing, Portal, Resume)
│   ├── api/                    # Django REST Framework views
│   └── job_finder/             # Django settings
├── fastapi_app/                # FastAPI application
│   ├── requirements.txt
│   ├── main.py                 # API endpoints & background tasks
│   ├── llm.py                  # Ollama client & prompt engineering
│   ├── scraper.py              # Portal scrapers
│   └── schemas.py              # Pydantic models
└── prompts.txt                 # LLM prompt templates
```

## Testing

This project uses **pytest** with **pytest-django** for comprehensive test coverage across both Django and FastAPI services.

### Test Configuration

- `pytest.ini` in job_finder/ for Django tests
- FastAPI tests use FastAPI TestClient with mocked dependencies
- Django tests use APIClient with force_authenticate()
- Background tasks are mocked in FastAPI tests to avoid external calls

### Test Coverage

#### Django Tests (job_finder/)

| Test File | Coverage |
|----------|----------|
| `job_finder/tasks/tests.py` | Task model |
| `job_finder/home/tests.py` | Models + Admin actions |
| `job_finder/api/tests.py` | Serializers + API views |
| `job_finder/accounts/tests.py` | CustomUser model |

#### FastAPI Tests (fastapi_app/tests/)

| Test File | Coverage |
|----------|----------|
| `fastapi_app/tests/test_schemas.py` | Pydantic models |
| `fastapi_app/tests/test_api.py` | API endpoints |

### Running Tests

#### Django Tests
```bash
# Run all Django tests via Docker
docker compose exec django pytest --reuse-db
```

#### FastAPI Tests
```bash
# Run FastAPI tests via Docker
docker compose exec fastapi_service pytest
```

## Future Enhancements

- [ ] Resume-Job Matching - AI-powered candidate-job fit scoring using stored resumes
- [ ] Explicit support for cloud gemini/open source models
- [ ] Email Notifications - Send new matches to candidates
- [ ] Web Dashboard - React/Vue frontend for visualization
- [ ] Additional Portals - Expand to NoFluffJobs, LinkedIn, etc.
- [ ] Caching Layer - Redis for frequently accessed queries
- [ ] CI/CD Pipeline - GitHub Actions for automated testing
