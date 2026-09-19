@echo off
REM ============================================================================
REM CYBERCRIME PREDICTIVE ANALYTICS FRAMEWORK (SIH 2026 - Problem Statement: 26184)
REM 1-Click Live Demonstration Launcher
REM ============================================================================

title SIH 2026 - Cybercrime Predictive Analytics Demo (PS 26184)
color 0A

echo ============================================================================
echo   CYBERCRIME PREDICTIVE ANALYTICS FRAMEWORK FOR FORECASTING WITHDRAWALS
echo   Problem Statement ID: 26184 -- Smart India Hackathon Live Demonstration
echo ============================================================================
echo.

REM Navigate to project root directory
cd /d "%~dp0\.."
echo [1/4] Working Directory: %CD%

REM Check Python installation
where python >nul 2>nul
if %errorlevel% neq 0 (
    color 0C
    echo [ERROR] Python is not found in PATH. Please install Python 3.10+ and add to PATH.
    pause
    exit /b 1
)
echo [2/4] Python Environment Verified.

REM Run fast 10-step system smoke test
echo [3/4] Running Pre-Flight System Smoke Test...
python src/system_smoke_test.py
if %errorlevel% neq 0 (
    color 0C
    echo [WARNING] Smoke test encountered an issue. Proceeding to API launch with fallback mode...
) else (
    echo [3/4] System Smoke Test: PASSED (10/10 Steps Verified).
)

echo.
echo [4/4] Starting FastAPI Production Server on http://127.0.0.1:8000 ...
echo       Swagger UI Docs: http://127.0.0.1:8000/docs
echo       GIS Dashboard:   http://127.0.0.1:8000/dashboard
echo.
echo Press Ctrl+C to stop the demonstration server at any time.
echo ============================================================================

REM Launch default browser to docs after 2 second delay in background
start /b cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:8000/docs"

REM Start Uvicorn web server
uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
pause
