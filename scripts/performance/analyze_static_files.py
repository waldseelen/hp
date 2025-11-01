#!/usr/bin/env python3
"""
Static files analysis script for CI/CD pipelines
Analyzes collectstatic output and generates detailed file size reports
"""

import json
import os
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path


class StaticFilesAnalyzer:
    """Analyze Django static files and generate size reports"""

    def __init__(self, static_root="staticfiles", output_dir="build-reports"):
        self.static_root = Path(static_root)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def get_file_sizes(self):
        """Get sizes of all files in static directory"""
        file_sizes = {}

        if not self.static_root.exists():
            print(f"Static root directory not found: {self.static_root}")
            return file_sizes

        for file_path in self.static_root.rglob("*"):
            if file_path.is_file():
                try:
                    size = file_path.stat().st_size
                    relative_path = file_path.relative_to(self.static_root)
                    file_sizes[str(relative_path)] = size
                except OSError as e:
                    print(f"Error getting size for {file_path}: {e}")

        return file_sizes

    def analyze_by_extension(self, file_sizes):
        """Analyze files grouped by extension"""
        ext_stats = defaultdict(lambda: {"count": 0, "total_size": 0, "files": []})

        for file_path, size in file_sizes.items():
            ext = Path(file_path).suffix.lower()
            if not ext:
                ext = "no_extension"

            ext_stats[ext]["count"] += 1
            ext_stats[ext]["total_size"] += size
            ext_stats[ext]["files"].append(
                {"path": file_path, "size": size, "size_kb": round(size / 1024, 2)}
            )

        # Sort files by size within each extension
        for ext_data in ext_stats.values():
            ext_data["files"].sort(key=lambda x: x["size"], reverse=True)

        return dict(ext_stats)

    def generate_report(self, file_sizes, ext_stats):
        """Generate comprehensive report"""
        total_files = len(file_sizes)
        total_size = sum(file_sizes.values())

        # Size thresholds for warnings
        LARGE_FILE_THRESHOLD = 1024 * 1024  # 1MB
        BUNDLE_THRESHOLD = 512 * 1024  # 512KB

        report = {
            "timestamp": datetime.now().isoformat(),
            "static_root": str(self.static_root),
            "summary": {
                "total_files": total_files,
                "total_size_bytes": total_size,
                "total_size_kb": round(total_size / 1024, 2),
                "total_size_mb": round(total_size / (1024 * 1024), 2),
            },
            "by_extension": {},
            "large_files": [],
            "warnings": [],
        }

        # Process extension stats
        for ext, data in ext_stats.items():
            report["by_extension"][ext] = {
                "count": data["count"],
                "total_size_bytes": data["total_size"],
                "total_size_kb": round(data["total_size"] / 1024, 2),
                "total_size_mb": round(data["total_size"] / (1024 * 1024), 2),
                "average_size_kb": (
                    round((data["total_size"] / data["count"]) / 1024, 2)
                    if data["count"] > 0
                    else 0
                ),
                "largest_files": data["files"][:5],  # Top 5 largest files
            }

        # Find large files
        for file_path, size in file_sizes.items():
            if size > LARGE_FILE_THRESHOLD:
                report["large_files"].append(
                    {
                        "path": file_path,
                        "size_bytes": size,
                        "size_mb": round(size / (1024 * 1024), 2),
                    }
                )

        # Generate warnings
        if total_size > 50 * 1024 * 1024:  # 50MB
            report["warnings"].append(
                {
                    "level": "high",
                    "message": f'Total static files size ({report["summary"]["total_size_mb"]:.1f}MB) exceeds recommended 50MB limit',
                }
            )

        # Check for large JS/CSS bundles
        js_files = [f for f in file_sizes.items() if f[0].endswith(".js")]
        css_files = [f for f in file_sizes.items() if f[0].endswith(".css")]

        for file_path, size in js_files + css_files:
            if size > BUNDLE_THRESHOLD:
                report["warnings"].append(
                    {
                        "level": "medium",
                        "message": f"Large bundle: {file_path} ({round(size/1024, 1)}KB) - consider code splitting",
                    }
                )

        return report

    def save_report(self, report, filename="static-files-report.json"):
        """Save report to file"""
        output_path = self.output_dir / filename
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"Static files report saved to: {output_path}")
        return output_path

    def print_summary(self, report):
        """Print human-readable summary"""
        print("📊 Django Static Files Analysis Report")
        print("=" * 50)
        print(f"Static Root: {report['static_root']}")
        print(f"Timestamp: {report['timestamp']}")
        print()

        summary = report["summary"]
        print("📈 Summary:")
        print(f"  Total Files: {summary['total_files']:,}")
        print(
            f"  Total Size: {summary['total_size_mb']:.2f} MB ({summary['total_size_kb']:.0f} KB)"
        )
        print()

        print("📁 By Extension (Top 5):")
        sorted_ext = sorted(
            report["by_extension"].items(),
            key=lambda x: x[1]["total_size_bytes"],
            reverse=True,
        )[:5]

        for ext, data in sorted_ext:
            print(f"  {ext}: {data['count']} files, {data['total_size_mb']:.2f} MB")

        print()

        if report["large_files"]:
            print("⚠️  Large Files (>1MB):")
            for file_info in report["large_files"][:5]:  # Show top 5
                print(f"  {file_info['path']}: {file_info['size_mb']:.2f} MB")

        if report["warnings"]:
            print()
            print("🚨 Warnings:")
            for warning in report["warnings"]:
                level_icon = "🔴" if warning["level"] == "high" else "🟡"
                print(f"  {level_icon} {warning['message']}")


def run_collectstatic_and_analyze():
    """Run collectstatic and analyze the results"""
    print("🔧 Running Django collectstatic...")

    # Run collectstatic
    try:
        result = subprocess.run(
            [sys.executable, "manage.py", "collectstatic", "--noinput", "--clear"],
            capture_output=True,
            text=True,
            check=True,
        )

        print("✅ collectstatic completed successfully")

        # Analyze static files
        analyzer = StaticFilesAnalyzer()
        file_sizes = analyzer.get_file_sizes()

        if not file_sizes:
            print("❌ No static files found to analyze")
            return 1

        ext_stats = analyzer.analyze_by_extension(file_sizes)
        report = analyzer.generate_report(file_sizes, ext_stats)

        # Save and print report
        analyzer.save_report(report)
        analyzer.print_summary(report)

        # Check for critical issues
        if report["warnings"]:
            high_warnings = [w for w in report["warnings"] if w["level"] == "high"]
            if high_warnings:
                print("\n❌ Critical issues found - review warnings above")
                return 1

        print("\n✅ Static files analysis completed successfully")
        return 0

    except subprocess.CalledProcessError as e:
        print(f"❌ collectstatic failed: {e.stderr}")
        return 1
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return 1


def main():
    """Main entry point"""
    exit_code = run_collectstatic_and_analyze()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
