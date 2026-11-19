@echo off
setlocal enabledelayedexpansion
title API Sentinel — Service Launcher

:: Ensure working directory is the script folder (api-sentinel root)
cd /d "%~dp0"

echo ================================================================
echo               API SENTINEL - SERVICE LAUNCHER
echo ================================================================
echo.

:: 1. Check for Backend Virtual Environment
if not exist "backend\venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found in backend\venv!
    echo Please create the virtual environment before running.
    echo.
    pause
    exit /b 1
)

:: 2. Check for .env file
if not exist "backend\.env" (
    if exist "backend\.env.example" (
        echo [INFO] Creating backend\.env from .env.example...
        copy "backend\.env.example" "backend\.env" >nul
    )
)

:: 3. Run Database Migrations
echo [1/3] Applying latest database migrations...
cd backend
call .\venv\Scripts\alembic.exe upgrade head
if errorlevel 1 (
    echo [ERROR] Database migration failed!
    cd ..
    pause
    exit /b 1
)

:: 4. Summary & Links
echo.
echo ================================================================
echo [2/3] API Sentinel Engine Initialized:
echo   * API Server:        http://127.0.0.1:8000
echo   * Swagger UI Docs:   http://127.0.0.1:8000/docs
echo   * ReDoc API Docs:    http://127.0.0.1:8000/redoc
echo   * Health Check:      http://127.0.0.1:8000/health
echo   * Background Worker: In-Process Async Monitor Scheduler
echo ================================================================
echo.

:: 5. Open Browser to API Documentation
start "" cmd /c "timeout /t 2 /nobreak >nul & start http://127.0.0.1:8000/docs"

:: 6. Launch FastAPI Server with Uvicorn
echo [3/3] Starting FastAPI server on http://127.0.0.1:8000 (Ctrl+C to stop)...
echo.
call .\venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000 --reload

cd ..
pause
