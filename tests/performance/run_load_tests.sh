#!/usr/bin/env bash
# Apache Bench Load Testing Script
# Reference: docs/monitoring/performance-monitoring.md

# Configuration
HOST="${1:-http://localhost:8000}"
RESULTS_DIR="tests/performance/results"

# Create results directory
mkdir -p "$RESULTS_DIR"

echo "======================================"
echo "Apache Bench Load Testing"
echo "Target: $HOST"
echo "Results: $RESULTS_DIR"
echo "======================================"
echo

# Test 1: Homepage Performance (Normal Load)
echo "[1/5] Testing Homepage (100 requests, concurrency 10)..."
ab -n 100 -c 10 -g "$RESULTS_DIR/home_normal.tsv" "$HOST/" > "$RESULTS_DIR/home_normal.txt"
echo "   ✅ Completed: $RESULTS_DIR/home_normal.txt"

# Test 2: Homepage Performance (High Load)
echo "[2/5] Testing Homepage (1000 requests, concurrency 50)..."
ab -n 1000 -c 50 -g "$RESULTS_DIR/home_peak.tsv" "$HOST/" > "$RESULTS_DIR/home_peak.txt"
echo "   ✅ Completed: $RESULTS_DIR/home_peak.txt"

# Test 3: Personal Page Performance
echo "[3/5] Testing Personal Page (500 requests, concurrency 25)..."
ab -n 500 -c 25 -g "$RESULTS_DIR/personal.tsv" "$HOST/personal/" > "$RESULTS_DIR/personal.txt"
echo "   ✅ Completed: $RESULTS_DIR/personal.txt"

# Test 4: Search API Performance (with keep-alive)
echo "[4/5] Testing Search API (500 requests, concurrency 20, keep-alive)..."
ab -n 500 -c 20 -k -H "X-Requested-With: XMLHttpRequest" \
   -g "$RESULTS_DIR/search_api.tsv" \
   "$HOST/api/search/?q=python" > "$RESULTS_DIR/search_api.txt"
echo "   ✅ Completed: $RESULTS_DIR/search_api.txt"

# Test 5: Health Check (Monitoring)
echo "[5/5] Testing Health Check (1000 requests, concurrency 10)..."
ab -n 1000 -c 10 -g "$RESULTS_DIR/health.tsv" "$HOST/health/" > "$RESULTS_DIR/health.txt"
echo "   ✅ Completed: $RESULTS_DIR/health.txt"

echo
echo "======================================"
echo "Load Testing Complete!"
echo "======================================"
echo
echo "📊 Performance Summary:"
echo

# Extract key metrics from results
for file in "$RESULTS_DIR"/*.txt; do
    echo "$(basename "$file" .txt):"
    grep "Requests per second:" "$file" || echo "  N/A"
    grep "Time per request:" "$file" | head -n 1 || echo "  N/A"
    grep "Failed requests:" "$file" || echo "  N/A"
    echo
done

echo "📁 Full results saved to: $RESULTS_DIR"
echo
echo "Next steps:"
echo "  1. Review detailed results in $RESULTS_DIR/*.txt"
echo "  2. Analyze response time distribution in $RESULTS_DIR/*.tsv"
echo "  3. Compare with baseline in docs/performance/baseline.md"
echo "  4. If performance degraded, run: python manage.py analyze_performance"
