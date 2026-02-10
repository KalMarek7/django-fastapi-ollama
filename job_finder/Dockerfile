# 1. Use a lightweight Python image
FROM python:3.12-slim

# 2. Set environment variables
# Prevents Python from writing .pyc files and keeps logs visible in Docker
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Set working directory
WORKDIR /app

# 4. Install system dependencies for Postgres and PDF tools
# libpq-dev is required for the psycopg2 (Postgres) driver
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 5. Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy the rest of the application code
COPY . .

# 7. Expose the port Django will run on
EXPOSE 8000

# 8. Run the server (can be overridden by docker-compose)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]