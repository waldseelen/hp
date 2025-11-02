# Apache Bench Load Testing Script (PowerShell)
# Reference: docs/monitoring/performance-monitoring.md

param(
    [string]$TargetHost = "http://localhost:8000",
    [string]$ResultsDir = "tests\performance\results"
)

# Create results directory
New-Item -ItemType Directory -Force -Path $ResultsDir | Out-Null

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Apache Bench Load Testing" -ForegroundColor Cyan
Write-Host "Target: $TargetHost" -ForegroundColor Cyan
Write-Host "Results: $ResultsDir" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Note: Apache Bench (ab.exe) must be installed
# Download from: https://www.apachelounge.com/download/
# Or use WSL: wsl ab -n 100 -c 10 ...

$tests = @(
    @{
        Name        = "Homepage (Normal Load)"
        Requests    = 100
        Concurrency = 10
        URL         = "$TargetHost/"
        Output      = "home_normal"
    },
    @{
        Name        = "Homepage (High Load)"
        Requests    = 1000
        Concurrency = 50
        URL         = "$TargetHost/"
        Output      = "home_peak"
    },
    @{
        Name        = "Personal Page"
        Requests    = 500
        Concurrency = 25
        URL         = "$TargetHost/personal/"
        Output      = "personal"
    },
    @{
        Name        = "Search API"
        Requests    = 500
        Concurrency = 20
        URL         = "$TargetHost/api/search/?q=python"
        Output      = "search_api"
        Headers     = @("-H", "X-Requested-With: XMLHttpRequest")
    },
    @{
        Name        = "Health Check"
        Requests    = 1000
        Concurrency = 10
        URL         = "$TargetHost/health/"
        Output      = "health"
    }
)

$testNum = 1
foreach ($test in $tests) {
    $totalTests = $tests.Count
    Write-Host "[$testNum/$totalTests] Testing $($test.Name) ($($test.Requests) requests, concurrency $($test.Concurrency))..." -ForegroundColor Yellow

    $outputFile = Join-Path $ResultsDir "$($test.Output).txt"
    $tsvFile = Join-Path $ResultsDir "$($test.Output).tsv"

    # Build ab command
    $abCmd = "ab -n $($test.Requests) -c $($test.Concurrency) -g `"$tsvFile`""

    if ($test.Headers) {
        $abCmd += " $($test.Headers -join ' ')"
    }

    $abCmd += " `"$($test.URL)`""

    # Execute with WSL if available, otherwise show error
    try {
        if (Get-Command wsl -ErrorAction SilentlyContinue) {
            Invoke-Expression "wsl $abCmd" | Out-File -FilePath $outputFile -Encoding utf8
            Write-Host "   ✅ Completed: $outputFile" -ForegroundColor Green
        }
        else {
            Write-Host "   ⚠️  WSL not found. Please install WSL or Apache Bench for Windows" -ForegroundColor Red
            Write-Host "      Command to run manually: $abCmd" -ForegroundColor Gray
        }
    }
    catch {
        Write-Host "   ❌ Error: $_" -ForegroundColor Red
    }

    $testNum++
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Load Testing Complete!" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "📊 Performance Summary:" -ForegroundColor Green
Write-Host ""

# Extract key metrics from results
Get-ChildItem -Path $ResultsDir -Filter "*.txt" | ForEach-Object {
    Write-Host "$($_.BaseName):" -ForegroundColor Yellow
    $content = Get-Content $_.FullName
    $rps = $content | Select-String "Requests per second:"
    $tpr = $content | Select-String "Time per request:" | Select-Object -First 1
    $failed = $content | Select-String "Failed requests:"

    if ($rps) { Write-Host "  $rps" }
    if ($tpr) { Write-Host "  $tpr" }
    if ($failed) { Write-Host "  $failed" }
    Write-Host ""
}

Write-Host "📁 Full results saved to: $ResultsDir" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Green
Write-Host "  1. Review detailed results in $ResultsDir\*.txt"
Write-Host "  2. Analyze response time distribution in $ResultsDir\*.tsv"
Write-Host "  3. Compare with baseline in docs\performance\baseline.md"
Write-Host "  4. If performance degraded, run: python manage.py analyze_performance"
