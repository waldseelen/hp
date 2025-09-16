@echo off
setlocal

REM -------------------------------
REM Git Automation Script
REM -------------------------------
REM This script automatically creates a commit message from the last completed
REM task in your roadmap.txt file and commits/pushes the changes.
REM
REM USAGE:
REM 1. Mark your completed tasks in roadmap.txt by starting the line
REM    with "# DONE:", for example:
REM    # DONE: ### Task 1.1: Initial Setup
REM 2. Run this script from your repository's root directory.
REM -------------------------------

REM -------------------------------
REM Configuration
REM -------------------------------
REM Use absolute path for roadmap
set "ROADMAP=D:\FILES\BEST\roadmap.txt"
REM Create message file in the same directory as the script for reliability
set "MSGFILE=%~dp0gitmsg.txt"

REM -------------------------------
REM Pre-flight checks
REM -------------------------------
if not exist "%ROADMAP%" (
    echo ERROR: Roadmap file not found at "%ROADMAP%".
    echo Please check the path.
    exit /b 1
)

REM Remove old temp file if it exists
if exist "%MSGFILE%" del "%MSGFILE%"

REM -------------------------------
REM PowerShell: read roadmap and build commit message
REM -------------------------------
powershell -NoProfile -Command ^
"try { ^
    $roadmapPath = '%ROADMAP%'; ^
    $msgPath = '%MSGFILE%'; ^
    Write-Host '--> Reading roadmap from:' $roadmapPath; ^
    if (-not (Test-Path $roadmapPath)) { throw ('Roadmap file not found at path: ' + $roadmapPath) } ^
    $lines = Get-Content -LiteralPath $roadmapPath -Encoding UTF8; ^
    $lastCompleted = -1; ^
    for ($i=0; $i -lt $lines.Count; $i++) { if ($lines[$i] -match '^# DONE:') { $lastCompleted = $i } } ^
    if ($lastCompleted -eq -1) { throw 'No completed tasks found. Mark completed tasks in roadmap.txt with ''# DONE:''' } ^
    $phaseIndex = -1; ^
    for ($i=$lastCompleted; $i -ge 0; $i--) { if ($lines[$i] -match 'PHASE') { $phaseIndex = $i; break } } ^
    if ($phaseIndex -eq -1) { $phaseIndex = $lastCompleted } ^
    $title = $lines[$phaseIndex].Trim(); ^
    Write-Host ('--> Found commit title: ' + $title); ^
    $endIndex = $lines.Count - 1; ^
    for ($j = $phaseIndex + 1; $j -lt $lines.Count; $j++) { if ($lines[$j] -match 'PHASE') { $endIndex = $j - 1; break } } ^
    $bodyLines = @(); ^
    for ($k = $phaseIndex + 1; $k -le $endIndex; $k++) { $bodyLines += $lines[$k] } ^
    $timestamp = (Get-Date).ToString('ddd dd.MM HH:mm'); ^
    $outputLines = @(); ^
    $outputLines += $title; ^
    $outputLines += ''; ^
    $outputLines += $bodyLines; ^
    $outputLines += ''; ^
    $outputLines += 'Commit Date: ' + $timestamp; ^
    Set-Content -Path $msgPath -Value $outputLines -Encoding UTF8; ^
    Write-Host '--> Commit message file successfully created at:' $msgPath; ^
    exit 0; ^
} catch { ^
    Write-Host ('[POWERSHELL ERROR] ' + $_.Exception.Message); ^
    exit 3; ^
}"

REM -------------------------------
REM Check PowerShell exit codes
REM -------------------------------
if errorlevel 3 (
    echo.
    echo [SCRIPT HALTED] PowerShell script failed to execute. See message above.
    exit /b 1
)

REM -------------------------------
REM Ensure commit message file exists and is not empty
REM -------------------------------
if not exist "%MSGFILE%" (
    echo.
    echo [SCRIPT HALTED] Commit message file was not created by PowerShell.
    exit /b 1
)
for %%A in ("%MSGFILE%") do if %%~zA==0 (
    echo.
    echo [SCRIPT HALTED] Commit message file is empty.
    del "%MSGFILE%" >nul 2>&1
    exit /b 1
)

REM -------------------------------
REM Show generated commit message
REM -------------------------------
echo.
echo ===== Generated Commit Message =====
type "%MSGFILE%"
echo ====================================
echo.

REM -------------------------------
REM Git status and confirmation
REM -------------------------------
for /f "tokens=*" %%i in ('git rev-parse --abbrev-ref HEAD') do set "current_branch=%%i"
echo --- Git Status ---
git status
echo ------------------
echo.
set /p proceed="==> Commit and push these changes to the '%current_branch%' branch? (Y/N): "
if /i not "%proceed%"=="Y" (
    echo.
    echo Operation cancelled by user.
    del "%MSGFILE%" >nul 2>&1
    exit /b 0
)

REM -------------------------------
REM Git add, commit, push
REM -------------------------------
echo.
echo --> Staging all changes...
git add .
echo --> Committing with generated message...
git commit -F "%MSGFILE%"
if errorlevel 1 (
    echo.
    echo [COMMIT FAILED] Please check the output above.
    del "%MSGFILE%" >nul 2>&1
    exit /b 1
)

echo --> Pushing to origin/%current_branch%...
git push origin %current_branch%
if errorlevel 1 (
    echo.
    echo [PUSH FAILED] Please check the output above.
    del "%MSGFILE%" >nul 2>&1
    exit /b 1
)

echo.
echo Operation completed successfully!
del "%MSGFILE%" >nul 2>&1
endlocal
exit /b 0
