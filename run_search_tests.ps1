#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Run search functionality tests

.DESCRIPTION
    Comprehensive test runner for search index, API, and admin integration tests.
    Requires MeiliSearch to be running for integration tests.

.PARAMETER TestType
    Type of tests to run: unit, integration, all, coverage

.PARAMETER Markers
    Pytest markers to filter tests (e.g., 'search', 'api', 'admin')

.PARAMETER Verbose
    Enable verbose output

.EXAMPLE
    .\run_search_tests.ps1 -TestType unit

.EXAMPLE
    .\run_search_tests.ps1 -TestType all -Verbose

.EXAMPLE
    .\run_search_tests.ps1 -Markers "search and api"
#>

param(
    [Parameter(Position = 0)]
    [ValidateSet('unit', 'integration', 'all', 'coverage', 'quick')]
    [string]$TestType = 'all',

    [Parameter()]
    [string]$Markers = '',

    [Parameter()]
    [switch]$Verbose,

    [Parameter()]
    [switch]$NoCoverage,

    [Parameter()]
    [int]$Parallel = 0
)

# Colors for output
$ColorReset = "`e[0m"
$ColorGreen = "`e[32m"
$ColorYellow = "`e[33m"
$ColorRed = "`e[31m"
$ColorBlue = "`e[34m"
$ColorCyan = "`e[36m"

function Write-ColorOutput {
    param([string]$Message, [string]$Color)
    Write-Host "$Color$Message$ColorReset"
}

function Test-MeiliSearch {
    Write-ColorOutput "🔍 Checking MeiliSearch status..." $ColorCyan
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:7700/health" -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            Write-ColorOutput "✓ MeiliSearch is running" $ColorGreen
            return $true
        }
    }
    catch {
        Write-ColorOutput "⚠ MeiliSearch is not running at localhost:7700" $ColorYellow
        Write-ColorOutput "  Integration tests may fail. Start with: docker-compose up -d meilisearch" $ColorYellow
        return $false
    }
    return $false
}

# Header
Write-Host ""
Write-ColorOutput "═══════════════════════════════════════════════════════════" $ColorBlue
Write-ColorOutput "   SEARCH FUNCTIONALITY TEST SUITE" $ColorBlue
Write-ColorOutput "═══════════════════════════════════════════════════════════" $ColorBlue
Write-Host ""

# Check MeiliSearch status
$meiliRunning = Test-MeiliSearch
Write-Host ""

# Build pytest command
$pytestArgs = @()

# Test selection
switch ($TestType) {
    'unit' {
        Write-ColorOutput "📦 Running Unit Tests (Search Index)" $ColorCyan
        $pytestArgs += 'tests/unit/test_search_index.py'
        $pytestArgs += '-m', 'unit'
    }
    'integration' {
        Write-ColorOutput "🔗 Running Integration Tests (API + Admin)" $ColorCyan
        $pytestArgs += 'tests/integration/test_search_api.py'
        $pytestArgs += 'tests/integration/test_admin_reindex.py'
        $pytestArgs += '-m', 'integration'
    }
    'quick' {
        Write-ColorOutput "⚡ Running Quick Tests (Unit only, no coverage)" $ColorCyan
        $pytestArgs += 'tests/unit/test_search_index.py'
        $pytestArgs += '-m', 'unit'
        $pytestArgs += '--no-cov'
        $NoCoverage = $true
    }
    'coverage' {
        Write-ColorOutput "📊 Running Full Test Suite with Coverage" $ColorCyan
        $pytestArgs += 'tests/unit/test_search_index.py'
        $pytestArgs += 'tests/integration/test_search_api.py'
        $pytestArgs += 'tests/integration/test_admin_reindex.py'
    }
    'all' {
        Write-ColorOutput "🎯 Running All Search Tests" $ColorCyan
        $pytestArgs += 'tests/unit/test_search_index.py'
        $pytestArgs += 'tests/integration/test_search_api.py'
        $pytestArgs += 'tests/integration/test_admin_reindex.py'
    }
}

# Custom markers
if ($Markers) {
    $pytestArgs += '-m', $Markers
}

# Verbosity
if ($Verbose) {
    $pytestArgs += '-vv'
}
else {
    $pytestArgs += '-v'
}

# Coverage
if (-not $NoCoverage -and $TestType -ne 'quick') {
    $pytestArgs += '--cov=apps.main'
    $pytestArgs += '--cov-report=term-missing'
    $pytestArgs += '--cov-report=html:htmlcov'
}

# Parallel execution
if ($Parallel -gt 0) {
    $pytestArgs += '-n', $Parallel
    Write-ColorOutput "⚙️  Using $Parallel parallel workers" $ColorCyan
}

# Additional pytest options
$pytestArgs += '--strict-markers'
$pytestArgs += '--tb=short'
$pytestArgs += '--color=yes'

Write-Host ""
Write-ColorOutput "Running: pytest $($pytestArgs -join ' ')" $ColorCyan
Write-Host ""
Write-ColorOutput "───────────────────────────────────────────────────────────" $ColorBlue
Write-Host ""

# Run tests
try {
    & pytest @pytestArgs
    $exitCode = $LASTEXITCODE

    Write-Host ""
    Write-ColorOutput "───────────────────────────────────────────────────────────" $ColorBlue
    Write-Host ""

    if ($exitCode -eq 0) {
        Write-ColorOutput "✓ All tests passed!" $ColorGreen

        # Show coverage report location
        if (-not $NoCoverage -and $TestType -ne 'quick') {
            Write-Host ""
            Write-ColorOutput "📊 Coverage Report: htmlcov/index.html" $ColorCyan
        }
    }
    else {
        Write-ColorOutput "✗ Some tests failed (exit code: $exitCode)" $ColorRed
        exit $exitCode
    }

}
catch {
    Write-ColorOutput "✗ Error running tests: $_" $ColorRed
    exit 1
}

Write-Host ""
Write-ColorOutput "═══════════════════════════════════════════════════════════" $ColorBlue
Write-Host ""

# Test Summary
Write-ColorOutput "Test Files:" $ColorBlue
Write-Host "  • tests/unit/test_search_index.py      - SearchIndexManager, sanitization, XSS"
Write-Host "  • tests/integration/test_search_api.py - API endpoints, pagination, rate limiting"
Write-Host "  • tests/integration/test_admin_reindex.py - Admin actions, signals, management command"
Write-Host ""

if (-not $meiliRunning) {
    Write-ColorOutput "💡 TIP: Start MeiliSearch for full integration tests:" $ColorYellow
    Write-Host "   docker-compose up -d meilisearch"
    Write-Host ""
}

exit $exitCode
