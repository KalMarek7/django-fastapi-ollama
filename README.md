# Job Scraper Engine | AI-Powered IT Job Aggregator

A production-ready full-stack application that scrapes job listings from major Polish IT portals, leverages local LLMs (Ollama) for intelligent job data extraction, and exposes everything through a robust REST API. Built with Django, FastAPI, and PostgreSQL.

## Purpose & Portfolio Value

This project demonstrates proficiency in:

- **Python Backend Development** - Django 5.x with Django REST Framework for robust API design
- **FastAPI & Async Processing** - High-performance background task handling
- **LLM Integration** - Local AI inference with Ollama for structured data extraction
- **Web Scraping** - Multi-portal data collection with BeautifulSoup4
- **System Architecture** - Docker Compose orchestration with PostgreSQL
- **Prompt Engineering** - Custom LLM prompts for job metadata extraction

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
| **Backend Framework** | Django 5.x, Django REST Framework, FastAPI |
| **Database** | PostgreSQL |
| **LLM** | Ollama (Llama 3.2) |
| **Scraping** | BeautifulSoup4, httpx |
| **Data Validation** | Pydantic v2 |
| **Containerization** | Docker, Docker Compose |
| **Python** | 3.11+ |

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
git clone https://github.com/yourusername/django-fastapi-cv.git
cd django-fastapi-cv
```

2. **Configure environment variables**

```bash
cp .env.example .env
# Edit .env with your database credentials
```

3. **Start all services**

```bash
docker-compose up --build
```

4. **Verify services are running**

| Service | URL | Description |
|---------|-----|-------------|
| Django API | http://localhost:8000 | REST API for job listings |
| FastAPI | http://localhost:8001 | Scraping engine endpoints |
| Ollama | http://localhost:11434 | LLM inference |

5. **Pull the LLM model (first time only)**

```bash
docker exec -it ollama ollama pull llama3.2
```

6. **Run Django migrations**

```bash
docker-compose exec django python manage.py migrate
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
    title: Optional[str] = None
    company: Optional[str] = None
    salary: Optional[str] = None
    years_of_experience: Optional[int] = None
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
docker compose exec django pytest job_finder/ --reuse-db
```

#### FastAPI Tests
```bash
# Run FastAPI tests via Docker
docker compose exec fastapi_service pytest fastapi_app/tests/ -v
```

## Future Enhancements

- [ ] Resume-Job Matching - AI-powered candidate-job fit scoring using stored resumes
- [ ] Explicit support for cloud gemini/open source models
- [ ] Email Notifications - Send new matches to candidates
- [ ] Web Dashboard - React/Vue frontend for visualization
- [ ] Additional Portals - Expand to NoFluffJobs, LinkedIn, etc.
- [ ] Caching Layer - Redis for frequently accessed queries
- [ ] CI/CD Pipeline - GitHub Actions for automated testing
