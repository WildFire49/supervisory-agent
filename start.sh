#!/bin/bash

# Exit on any error
set -e

echo "Starting Supervisory Agent..."

# Function to wait for database
wait_for_db() {
    echo "Waiting for PostgreSQL to be ready..."
    while ! pg_isready -h postgres-db -p 5432 -U vaishakh -d supervisory_agent; do
        echo "PostgreSQL is unavailable - sleeping"
        sleep 2
    done
    echo "PostgreSQL is ready!"
}

# Install postgresql-client for pg_isready
apt-get update && apt-get install -y postgresql-client

# Wait for database to be ready
wait_for_db

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start the application
echo "Starting FastAPI application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
