@echo off
REM Quick Start Script for Lluch Regulation Composite Management System (Windows)

echo ==================================
echo Lluch Regulation - Quick Start
echo ==================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo Docker is not running. Please start Docker Desktop first.
    pause
    exit /b 1
)

echo Docker is running
echo.

REM Create .env file if it doesn't exist
if not exist backend\.env (
    echo Creating backend\.env file...
    (
        echo DATABASE_URL=postgresql://lluch_user:lluch_pass@postgres:5432/lluch_regulation
        echo API_V1_PREFIX=/api
        echo PROJECT_NAME=Lluch Regulation - Composite Management
        echo DEBUG=True
        echo SECRET_KEY=dev-secret-key-change-in-production
        echo ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
        echo REDIS_URL=redis://redis:6379/0
        echo CELERY_BROKER_URL=redis://redis:6379/0
        echo CELERY_RESULT_BACKEND=redis://redis:6379/0
        echo MAX_UPLOAD_SIZE=10485760
        echo UPLOAD_DIR=/app/data/uploads
        echo COMPOSITE_THRESHOLD_PERCENT=5.0
        echo REVIEW_PERIOD_DAYS=90
    ) > backend\.env
    echo Created backend\.env file
) else (
    echo backend\.env already exists
)

echo.
echo Starting Docker containers...
docker-compose up -d

echo.
echo Waiting for services to be ready...
timeout /t 10 /nobreak >nul

echo.
echo Applying database migrations...
docker-compose exec -T backend alembic upgrade head

echo.
echo Generating dummy data...
docker-compose exec -T backend python -m app.scripts.generate_dummy_data

echo.
echo ==================================
echo Setup Complete!
echo ==================================
echo.
echo Access the application:
echo   Frontend:  http://localhost:5173
echo   API:       http://localhost:8000
echo   API Docs:  http://localhost:8000/docs
echo.
echo Login credentials:
echo   Admin:      admin / admin123
echo   Technician: tech_maria / tech123
echo   Viewer:     viewer / viewer123
echo.
echo Documentation:
echo   Getting Started: GETTING_STARTED.md
echo   Architecture:    ARCHITECTURE.md
echo.
echo Useful commands:
echo   View logs:       docker-compose logs -f
echo   Stop services:   docker-compose down
echo   Restart:         docker-compose restart
echo.
echo Happy coding!
echo.
pause






