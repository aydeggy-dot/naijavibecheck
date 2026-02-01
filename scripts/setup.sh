#!/bin/bash
# NaijaVibeCheck Setup Script

set -e

echo "🚀 Setting up NaijaVibeCheck..."

# Check for required tools
command -v docker >/dev/null 2>&1 || { echo "Docker is required but not installed. Aborting."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || command -v docker compose >/dev/null 2>&1 || { echo "Docker Compose is required but not installed. Aborting."; exit 1; }

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your configuration before continuing."
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p backend/sessions
mkdir -p backend/generated_media
mkdir -p templates/fonts
mkdir -p templates/backgrounds
mkdir -p templates/overlays
mkdir -p templates/elements

# Start Docker services
echo "🐳 Starting Docker services..."
docker-compose up -d db redis

# Wait for database to be ready
echo "⏳ Waiting for database..."
sleep 5

# Run database migrations
echo "📊 Running database migrations..."
docker-compose run --rm backend alembic upgrade head

# Seed initial data (optional)
read -p "Would you like to seed initial celebrity data? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🌱 Seeding database..."
    docker-compose run --rm backend python /app/../scripts/seed_celebrities.py
fi

# Start all services
echo "🚀 Starting all services..."
docker-compose up -d

echo ""
echo "✅ Setup complete!"
echo ""
echo "📍 Services running:"
echo "   - API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo "   - Database: localhost:5432"
echo "   - Redis: localhost:6379"
echo ""
echo "📋 Next steps:"
echo "   1. Edit .env with your Anthropic API key and Instagram credentials"
echo "   2. Add celebrities to track via the API or dashboard"
echo "   3. Monitor logs: docker-compose logs -f"
echo ""
