@echo off
setlocal enabledelayedexpansion

REM Full path to roadmap.txt
set "ROADMAP=D:\FILES\BEST\roadmap.txt"

REM Find the last completed task
set "LAST_TASK="
for /f "delims=" %%A in ('type "%ROADMAP%" ^| findstr /b "# ✅"') do (
    set "LAST_TASK=%%A"
)

REM Remove the "# ✅ " prefix
set "LAST_TASK=!LAST_TASK:# ✅ =!"

REM Check if a task was found
if "!LAST_TASK!"=="" (
    echo No completed tasks found in roadmap file.
    exit /b 1
)

REM Get current date and time
for /f "tokens=1-3 delims=/ " %%D in ("%DATE%") do (
    set "YYYY=%%F"
    set "MM=%%D"
    set "DD=%%E"
)
set "TIME_NOW=%TIME%"
set "DATETIME=%YYYY%-%MM%-%DD% %TIME_NOW%"

REM Check Git status
git status
echo.
set /p proceed="Do you want to commit and push these changes? (Y/N): "
if /i not "!proceed!"=="Y" (
    echo Operation cancelled.
    exit /b 0
)

REM Git operations
git add .
git commit -m "Latest progress / last task: !LAST_TASK! | %DATETIME%"
git push origin main
echo Operation completed.
