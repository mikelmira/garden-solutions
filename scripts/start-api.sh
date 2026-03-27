#!/bin/bash
# Garden Solutions API — Start script
# Usage: ./scripts/start-api.sh [--prod]

set -e

cd "$(dirname "$0")/../apps/api"

# Activate virtual environment if it exists
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Check if production mode
if [ "$1" = "--prod" ] || [ "$ENVIRONMENT" = "production" ]; then
    echo "Starting API in PRODUCTION mode..."
    exec uvicorn app.main:app \
        --host 0.0.0.0 \
        --port "${API_PORT:-8000}" \
        --workers "${API_WORKERS:-2}" \
        --log-level info
else
    echo "Starting API in DEVELOPMENT mode..."
    exec uvicorn app.main:app \
        --host 0.0.0.0 \
        --port "${API_PORT:-8000}" \
        --reload \
        --reload-exclude '.venv' \
        --log-level info
fi
