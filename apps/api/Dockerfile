FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .

# Copy application code
COPY . .

# Create uploads directory
RUN mkdir -p /app/uploads

# Railway injects PORT; default to 8000 for local dev
ENV PORT=8000
EXPOSE ${PORT}

# Run with uvicorn using the PORT env var (1 worker for trial plan memory limits)
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers 1
