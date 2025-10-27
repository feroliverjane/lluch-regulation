#!/bin/bash

# Quick Start Script for Lluch Regulation Composite Management System
# This script helps you get started quickly

set -e  # Exit on error

echo "=================================="
echo "Lluch Regulation - Quick Start"
echo "=================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo ""

# Create .env file if it doesn't exist
if [ ! -f backend/.env ]; then
    echo "📝 Creating backend/.env file..."
    cat > backend/.env << 'EOF'
DATABASE_URL=postgresql://lluch_user:lluch_pass@postgres:5432/lluch_regulation
API_V1_PREFIX=/api
PROJECT_NAME=Lluch Regulation - Composite Management
DEBUG=True
SECRET_KEY=dev-secret-key-change-in-production
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
MAX_UPLOAD_SIZE=10485760
UPLOAD_DIR=/app/data/uploads
COMPOSITE_THRESHOLD_PERCENT=5.0
REVIEW_PERIOD_DAYS=90
EOF
    echo "✅ Created backend/.env file"
else
    echo "✅ backend/.env already exists"
fi

echo ""
echo "🚀 Starting Docker containers..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

echo ""
echo "📊 Applying database migrations..."
docker-compose exec -T backend alembic upgrade head

echo ""
echo "🎲 Generating dummy data..."
docker-compose exec -T backend python -m app.scripts.generate_dummy_data

echo ""
echo "=================================="
echo "✅ Setup Complete!"
echo "=================================="
echo ""
echo "🌐 Access the application:"
echo "   Frontend:  http://localhost:5173"
echo "   API:       http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo ""
echo "👤 Login credentials:"
echo "   Admin:      admin / admin123"
echo "   Technician: tech_maria / tech123"
echo "   Viewer:     viewer / viewer123"
echo ""
echo "📚 Documentation:"
echo "   Getting Started: GETTING_STARTED.md"
echo "   Architecture:    ARCHITECTURE.md"
echo ""
echo "🛠  Useful commands:"
echo "   View logs:       docker-compose logs -f"
echo "   Stop services:   docker-compose down"
echo "   Restart:         docker-compose restart"
echo ""
echo "Happy coding! 🎉"








