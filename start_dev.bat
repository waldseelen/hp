@echo off
echo *** Django Development Server Starting...
echo.

REM Check if virtual environment exists and activate it
if exist "venv\Scripts\activate.bat" (
    echo [+] Activating virtual environment...
    call venv\Scripts\activate.bat

    REM Check if psutil is installed in virtual environment
    python -c "import psutil" 2>nul
    if errorlevel 1 (
        echo [!] psutil not found in virtual environment! Installing...
        pip install psutil
    )
) else (
    echo [!]  Virtual environment not found, using system Python
    REM Check if psutil is installed in system Python
    python -c "import psutil" 2>nul
    if errorlevel 1 (
        echo [!] psutil not found! Installing...
        pip install psutil
    )
)

REM Check if Django is installed
python -c "import django" 2>nul
if errorlevel 1 (
    echo [!] Django not found! Installing requirements...
    pip install -r requirements.txt
)

REM Collect static files (suppress output)
echo -> Collecting static files...
python manage.py collectstatic --noinput > nul 2>&1

REM Start the Django server
echo -> Starting Django server at http://127.0.0.1:8000
echo.
echo >> Press Ctrl+C to stop the server
echo.

REM Start server and open browser
start http://127.0.0.1:8000
timeout /t 2 /nobreak > nul

REM Start the Django server (single instance)
.\venv\Scripts\python.exe manage.py runserver