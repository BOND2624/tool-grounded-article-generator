FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for some Python packages (bcrypt, psycopg2, etc.)
RUN apt-get update && \
    apt-get install -y build-essential libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt

# Copy application code
COPY . .

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

# Use Uvicorn to serve FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

