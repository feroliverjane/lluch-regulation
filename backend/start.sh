#!/bin/bash

# Railway startup script
echo "🚀 Starting Lluch Regulation Backend..."

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Run database migrations
echo "🗄️ Running database migrations..."
alembic upgrade head

# Generate dummy data if needed
echo "📊 Generating initial data..."
python -m app.scripts.generate_dummy_data

# Start the application
echo "🌟 Starting FastAPI server..."
uvicorn app.main:app --host 0.0.0.0 --port $PORT


