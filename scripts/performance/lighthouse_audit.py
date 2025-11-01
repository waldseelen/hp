#!/usr/bin/env python3
"""
Performance measurement script for Lighthouse metrics
Measures FCP (First Contentful Paint) and TTI (Time to Interactive) before/after optimizations
"""

import json
import os
import statistics
import subprocess
import sys
from datetime import datetime
from pathlib import Path


class LighthouseRunner:
    """Run Lighthouse performance audits and extract key metrics"""

    def __init__(self, urls=None, output_dir="performance-reports"):
        self.urls = urls or [
            "http://localhost:8000/",
            "http://localhost:8000/personal/",
            "http://localhost:8000/blog/",
            "http://localhost:8000/tools/",
        ]
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def run_audit(self, url, output_file=None):
        """Run Lighthouse audit for a single URL"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            url_slug = url.replace("http://", "").replace("/", "_").replace(":", "")
            output_file = self.output_dir / f"lighthouse_{url_slug}_{timestamp}.json"

        cmd = [
            "npx",
            "lighthouse",
            url,
            "--output=json",
            f"--output-path={output_file}",
            "--only-categories=performance",
            "--chrome-flags=--headless --no-sandbox --disable-dev-shm-usage",
            "--quiet",
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                return str(output_file)
            else:
                print(f"Lighthouse failed for {url}: {result.stderr}")
                return None
        except subprocess.TimeoutExpired:
            print(f"Lighthouse timed out for {url}")
            return None
        except FileNotFoundError:
            print("Lighthouse not found. Install with: npm install -g lighthouse")
            return None

    def extract_metrics(self, report_file):
        """Extract key performance metrics from Lighthouse report"""
        try:
            with open(report_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            audits = data.get("audits", {})

            metrics = {
                "url": data.get("finalUrl", ""),
                "timestamp": datetime.now().isoformat(),
                "performance_score": data.get("categories", {})
                .get("performance", {})
                .get("score", 0)
                * 100,
                # Core Web Vitals
                "first_contentful_paint": audits.get("first-contentful-paint", {}).get(
                    "numericValue", 0
                ),
                "largest_contentful_paint": audits.get(
                    "largest-contentful-paint", {}
                ).get("numericValue", 0),
                "first_input_delay": audits.get("max-potential-fid", {}).get(
                    "numericValue", 0
                ),
                "cumulative_layout_shift": audits.get(
                    "cumulative-layout-shift", {}
                ).get("numericValue", 0),
                # Additional metrics
                "time_to_interactive": audits.get("interactive", {}).get(
                    "numericValue", 0
                ),
                "speed_index": audits.get("speed-index", {}).get("numericValue", 0),
                "total_blocking_time": audits.get("total-blocking-time", {}).get(
                    "numericValue", 0
                ),
                # Resource metrics
                "total_byte_weight": audits.get("total-byte-weight", {}).get(
                    "numericValue", 0
                ),
                "network_requests": audits.get("network-requests", {}).get(
                    "numericValue", 0
                ),
            }

            return metrics

        except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
            print(f"Error extracting metrics from {report_file}: {e}")
            return None

    def run_all_audits(self):
        """Run audits for all configured URLs"""
        results = []

        for url in self.urls:
            print(f"Running Lighthouse audit for: {url}")
            report_file = self.run_audit(url)

            if report_file:
                metrics = self.extract_metrics(report_file)
                if metrics:
                    results.append(metrics)
                    print(f"✅ Audit completed for {url}")
                else:
                    print(f"❌ Failed to extract metrics for {url}")
            else:
                print(f"❌ Audit failed for {url}")

        return results

    def generate_report(self, results, output_file="performance-summary.json"):
        """Generate a summary report from all audit results"""
        if not results:
            print("No results to report")
            return

        # Calculate averages
        summary = {
            "audit_timestamp": datetime.now().isoformat(),
            "total_urls": len(results),
            "average_scores": {},
            "individual_results": results,
        }

        # Metrics to average
        metrics_to_average = [
            "performance_score",
            "first_contentful_paint",
            "largest_contentful_paint",
            "first_input_delay",
            "cumulative_layout_shift",
            "time_to_interactive",
            "speed_index",
            "total_blocking_time",
            "total_byte_weight",
            "network_requests",
        ]

        for metric in metrics_to_average:
            values = [r[metric] for r in results if r.get(metric, 0) > 0]
            if values:
                summary["average_scores"][metric] = {
                    "mean": round(statistics.mean(values), 2),
                    "median": round(statistics.median(values), 2),
                    "min": round(min(values), 2),
                    "max": round(max(values), 2),
                }

        # Save summary
        output_path = self.output_dir / output_file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        print(f"Performance report saved to: {output_path}")

        # Print summary to console
        print("\n📊 Performance Summary:")
        print(f"URLs tested: {summary['total_urls']}")
        if "performance_score" in summary["average_scores"]:
            score = summary["average_scores"]["performance_score"]
            print(f"Average Performance Score: {score['mean']:.1f}/100")
        if "first_contentful_paint" in summary["average_scores"]:
            fcp = summary["average_scores"]["first_contentful_paint"]
            print(f"Average FCP: {fcp['mean']:.0f}ms")
        if "time_to_interactive" in summary["average_scores"]:
            tti = summary["average_scores"]["time_to_interactive"]
            print(f"Average TTI: {tti['mean']:.0f}ms")

        return summary


def main():
    """Main entry point"""
    print("🚀 Starting Lighthouse Performance Audit")

    # Check if Lighthouse is available
    try:
        subprocess.run(
            ["npx", "lighthouse", "--version"], capture_output=True, check=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Lighthouse not found. Install with: npm install -g lighthouse")
        sys.exit(1)

    # Run audits
    runner = LighthouseRunner()
    results = runner.run_all_audits()

    if results:
        summary = runner.generate_report(results)
        print("✅ Performance audit completed successfully")
        return 0
    else:
        print("❌ No audit results generated")
        return 1


if __name__ == "__main__":
    sys.exit(main())
