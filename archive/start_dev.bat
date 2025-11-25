
        echo [!] Using system Python
    )
)

REM Check Python version
python --version 2>nul
if errorlevel 1 (
    echo [X] Python not found! Please install Python first.
    pause
    exit /b 1
)

REM Check if requirements.txt exists and install dependencies
if exist "requirements.txt" (
    echo [+] Installing dependencies from requirements.txt...
    pip install -r requirements.txt --quiet
    if errorlevel 1 (
        echo [!] Some packages failed to install, but continuing...
        echo [!] Tip: Some packages need extra system dependencies
    ) else (
        echo [✓] Dependencies installed successfully
    )
) else (
    echo [!] requirements.txt not found!
)

REM Check if manage.py exists
if not exist "manage.py" (
    echo [X] manage.py not found! Are you in the correct directory?
    echo [?] Current directory: %CD%
    pause
    exit /b 1
)

REM Apply any pending migrations (skip if development environment is incomplete)
echo [+] Checking for database migrations...
python manage.py migrate --no-input >nul 2>&1
if errorlevel 1 (
    echo [!] Skipping migrations - development environment may be incomplete
    echo [!] To retry migrations later, run: python manage.py migrate
) else (
    echo [✓] Migrations applied successfully
)

REM Collect static files
echo [+] Collecting static files...
python manage.py collectstatic --noinput >nul 2>&1
if errorlevel 1 (
    echo [!] Static files collection skipped (may be missing packages)...
) else (
    echo [✓] Static files collected
)

REM Check if .env file exists
if exist ".env" (
    echo [✓] Environment file found
) else (
    echo [!] .env file not found - using default settings
)

echo.
echo ========================================
echo [✓] Pre-flight checks complete!
echo ========================================
echo.
echo [+] Starting Django development server...
echo [+] Server will be available at: http://127.0.0.1:8000
echo [+] Admin panel at: http://127.0.0.1:8000/admin
echo.
echo [?] Press Ctrl+C to stop the server
echo.

REM Open browser after a short delay
start "" http://127.0.0.1:8000
timeout /t 3 /nobreak > nul

REM Start the Django server with better error handling
python manage.py runserver 127.0.0.1:8000
if errorlevel 1 (
    echo.
    echo [X] Server failed to start!
    echo [?] Check the error messages above
    pause
    exit /b 1
)

REM This will only run if the server stops normally
echo.
echo [✓] Server stopped successfully
pause
