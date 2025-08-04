#!/bin/bash

# Supervisory Agent Docker Setup Script
# This script builds and runs the complete supervisory agent with PostgreSQL

set -e

echo "🚀 Starting Supervisory Agent Setup..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found! Please create it with your configuration."
    exit 1
fi

echo "📦 Building Docker images..."
docker-compose build

echo "🗄️  Starting PostgreSQL database..."
docker-compose up -d postgres-db

echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 10

echo "🚀 Starting Supervisory Agent application..."
docker-compose up -d supervisory-agent

echo "📊 Checking service status..."
docker-compose ps

echo "📝 Viewing logs (press Ctrl+C to stop)..."
echo "   - PostgreSQL logs: docker-compose logs postgres-db"
echo "   - Application logs: docker-compose logs supervisory-agent"
echo "   - All logs: docker-compose logs -f"

echo ""
echo "✅ Setup complete!"
echo "🌐 Application available at: http://localhost:8000"
echo "🗄️  Database available at: localhost:5432"
echo ""
echo "Useful commands:"
echo "  - Stop services: docker-compose down"
echo "  - View logs: docker-compose logs -f"
echo "  - Restart app: docker-compose restart supervisory-agent"
echo "  - Access database: docker-compose exec postgres-db psql -U vaishakh -d supervisory_agent"
