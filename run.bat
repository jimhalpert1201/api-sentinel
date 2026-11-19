@echo off
setlocal enabledelayedexpansion
title API Sentinel — Service Launcher

:: Ensure working directory is the script folder (api-sentinel root)
cd /d "%~dp0"

echo ================================================================
echo               API SENTINEL - FULL STACK LAUNCHER
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
echo [1/4] Applying latest database migrations...
cd backend
call .\venv\Scripts\alembic.exe upgrade head
if errorlevel 1 (
    echo [ERROR] Database migration failed!
    cd ..
    pause
    exit /b 1
)
cd ..

:: 4. Check Frontend Dependencies
echo.
echo [2/4] Verifying frontend dependencies...
if not exist "frontend\node_modules" (
    echo [INFO] Installing frontend packages (first run)...
    cd frontend
    call npm install
    cd ..
)

:: 5. Summary & Links
echo.
echo ================================================================
echo [3/4] API Sentinel Fleet Ready:
echo   * Web Dashboard:     http://localhost:5173
echo   * API Server:        http://127.0.0.1:8000
echo   * Swagger UI Docs:   http://127.0.0.1:8000/docs
echo   * ReDoc API Docs:    http://127.0.0.1:8000/redoc
echo   * Health Check:      http://127.0.0.1:8000/health
echo   * Background Worker: In-Process Async Monitor Scheduler
echo ================================================================
echo.

:: 6. Launch Frontend Dev Server in Separate Console Window
echo Starting Frontend (Vite) in background window...
start "API Sentinel - Web Dashboard (Vite)" cmd /c "cd /d \"%~dp0frontend\" && npm run dev"

:: 7. Open Browser to Dashboard
start "" cmd /c "timeout /t 3 /nobreak >nul & start http://localhost:5173"

:: 8. Launch FastAPI Server in Main Window
echo [4/4] Starting FastAPI server on http://127.0.0.1:8000 (Ctrl+C to stop)...
echo.
cd backend
call .\venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000 --reload

cd ..
pause
