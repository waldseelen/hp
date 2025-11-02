@echo off
cd /d "D:\FİLES\BEST"
echo Django hızlı başlatma...

REM Kill existing Django processes
taskkill /f /im python.exe 2>nul

REM Install only essential packages
pip install Django==5.1 python-decouple

REM Quick migrate without checks
python manage.py migrate --run-syncdb --verbosity=0

REM Start server directly
echo.
echo ========================================
echo Site başlatılıyor: http://localhost:8000
echo ========================================
python manage.py runserver 8000 --noreload --skip-checks
