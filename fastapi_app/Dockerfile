FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# Note: FastAPI usually runs on 8000, 
# but inside the Docker network, there's no conflict with Django 
# because they have different IP addresses (service names).
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000" ,"--reload"]