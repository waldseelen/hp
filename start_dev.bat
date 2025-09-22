@echo off
title Django Development Server
color 0A
echo.
echo ========================================
echo     Django Development Server
echo ========================================
echo.

REM Function to check if port 8000 is in use
for /f "tokens=5" %%a in ('netstat -an ^| findstr ":8000"') do (
    echo [!] Port 8000 is already in use!
    echo [!] Stopping existing Django processes...
    taskkill /f /im python.exe >nul 2>&1
    timeout /t 2 /nobreak > nul
)

REM Check if virtual environment exists and activate it
if exist "venv\Scripts\activate.bat" (
    echo [+] Activating virtual environment...
    call venv\Scripts\activate.bat
    echo [✓] Virtual environment activated
) else (
    echo [!] Virtual environment not found!
    echo [?] Would you like to create one? (Y/N)
    set /p create_venv=
    if /i "%create_venv%"=="Y" (
        echo [+] Creating virtual environment...
        python -m venv venv
        call venv\Scripts\activate.bat
        echo [✓] Virtual environment created and activated
    ) else (
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
    echo [+] Checking dependencies...
    python -c "import django" 2>nul
    if errorlevel 1 (
        echo [!] Django not found! Installing requirements...
        pip install -r requirements.txt
        if errorlevel 1 (
            echo [X] Failed to install requirements!
            pause
            exit /b 1
        )
        echo [✓] Dependencies installed successfully
    ) else (
        echo [✓] Django is available
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

REM Apply any pending migrations
echo [+] Checking for database migrations...
python manage.py migrate --check >nul 2>&1
if errorlevel 1 (
    echo [!] Applying database migrations...
    python manage.py migrate
    if errorlevel 1 (
        echo [X] Migration failed!
        pause
        exit /b 1
    )
    echo [✓] Migrations applied successfully
) else (
    echo [✓] Database is up to date
)

REM Collect static files
echo [+] Collecting static files...
python manage.py collectstatic --noinput >nul 2>&1
if errorlevel 1 (
    echo [!] Static files collection failed (continuing anyway...)
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