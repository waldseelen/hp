#!/usr/bin/env python3
"""
Code formatting script for UI/UX components
Automatically formats all code according to project standards
"""

import subprocess
import sys
from pathlib import Path

# Get project root
PROJECT_ROOT = Path(__file__).parent.parent


def run_command(command: list, description: str) -> bool:
    """Run a command and return success status"""
    print(f"\n🔧 {description}")
    print(f"Running: {' '.join(command)}")

    try:
        result = subprocess.run(
            command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=True
        )
        print(f"✅ {description} completed")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False


def main():
    """Run all formatting tools"""
    print("🎨 Starting code formatting for UI/UX components...")

    formatters = [
        # Python formatting
        (["black", "apps/", "tests/"], "Black code formatting"),
        (["isort", "apps/", "tests/"], "Import sorting"),
        # Remove unused imports
        (
            [
                "autoflake",
                "--remove-all-unused-imports",
                "--in-place",
                "--recursive",
                "apps/",
            ],
            "Remove unused imports",
        ),
    ]

    failed_formatters = []

    for command, description in formatters:
        if not run_command(command, description):
            failed_formatters.append(description)

    # Summary
    print("\n" + "=" * 60)
    if failed_formatters:
        print("❌ Some formatting failed:")
        for formatter in failed_formatters:
            print(f"  - {formatter}")
        sys.exit(1)
    else:
        print("✅ All code formatting completed!")
        print("🎉 Your code is now properly formatted!")

    # Optional: Run lint check after formatting
    print("\n🔍 Running lint check after formatting...")
    lint_result = subprocess.run([sys.executable, "scripts/lint.py"], cwd=PROJECT_ROOT)
    if lint_result.returncode == 0:
        print("✅ All quality checks pass after formatting!")
    else:
        print("⚠️  Some quality issues remain. Please review and fix manually.")


if __name__ == "__main__":
    main()
