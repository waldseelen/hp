#!/usr/bin/env python3
"""
Code quality and linting script for UI/UX components
Runs all code quality checks in sequence
"""

import os
import subprocess
import sys
from pathlib import Path

# Get project root
PROJECT_ROOT = Path(__file__).parent.parent


def run_command(command: list, description: str) -> bool:
    """Run a command and return success status"""
    print(f"\n🔍 {description}")
    print(f"Running: {' '.join(command)}")

    try:
        result = subprocess.run(
            command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=True
        )
        print(f"✅ {description} passed")
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
    """Run all code quality checks"""
    print("🚀 Starting code quality checks for UI/UX components...")

    checks = [
        # Python formatting
        (["black", "--check", "apps/", "tests/"], "Black formatting check"),
        (["isort", "--check-only", "apps/", "tests/"], "Import sorting check"),
        (["flake8", "apps/", "tests/"], "Flake8 linting"),
        # Type checking
        (["mypy", "apps/main/views/"], "Type checking"),
        # Security
        (["bandit", "-r", "apps/", "-x", "*/tests/*"], "Security check"),
        # Documentation
        (["pydocstyle", "apps/main/views/"], "Documentation style check"),
        # Django checks
        (["python", "manage.py", "check"], "Django system check"),
        (["python", "manage.py", "check", "--deploy"], "Django deployment check"),
    ]

    failed_checks = []

    for command, description in checks:
        if not run_command(command, description):
            failed_checks.append(description)

    # Summary
    print("\n" + "=" * 60)
    if failed_checks:
        print("❌ Some checks failed:")
        for check in failed_checks:
            print(f"  - {check}")
        print("\n💡 Fix the issues above and run the script again.")
        sys.exit(1)
    else:
        print("✅ All code quality checks passed!")
        print("🎉 Your UI/UX code meets quality standards!")


if __name__ == "__main__":
    main()
