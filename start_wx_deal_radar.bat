@echo off
setlocal

cd /d "%~dp0"

set "PORT=18501"
set "URL=http://localhost:%PORT%"

echo ========================================
echo wx-deal-radar
echo ========================================
echo.
echo Working directory: %CD%
echo Local URL: %URL%
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python was not found in PATH.
  echo Please install Python or add it to PATH first.
  pause
  exit /b 1
)

python -c "import streamlit" >nul 2>nul
if errorlevel 1 (
  echo [INFO] Streamlit is not installed. Installing requirements...
  python -m pip install -r requirements.txt
  if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
  )
)

echo [INFO] Opening browser...
start "" "%URL%"

echo [INFO] Starting Streamlit server. Press Ctrl+C to stop.
echo.
python -m streamlit run streamlit_app.py --server.port %PORT% --server.headless true

echo.
echo [INFO] Server stopped.
pause
