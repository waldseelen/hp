#!/usr/bin/env python3
"""
Project Cleanup Audit for Phase 10
"""

import os
from pathlib import Path


def find_unused_files():
    print("Scanning for potentially unused files...")

    unused_candidates = []

    # Check for common temp/backup patterns
    patterns = [
        "*.tmp",
        "*.bak",
        "*.backup",
        "*.old",
        "*~",
        "*.log",
        "*.cache",
        "*.pyc",
        "*.pyo",
        ".DS_Store",
        "Thumbs.db",
        "desktop.ini",
    ]

    for pattern in patterns:
        matches = list(Path(".").rglob(pattern))
        unused_candidates.extend(matches)

    # Check for empty directories
    empty_dirs = []
    for root, dirs, files in os.walk("."):
        for dir in dirs:
            dir_path = Path(root) / dir
            try:
                if not any(dir_path.iterdir()):
                    empty_dirs.append(dir_path)
            except:
                pass

    return unused_candidates, empty_dirs


def check_duplicate_files():
    print("Checking for potential duplicate files...")

    # Look for backup directories
    backup_dirs = []
    for item in Path(".").iterdir():
        if item.is_dir():
            name = item.name.lower()
            if any(
                keyword in name
                for keyword in ["backup", "old", "unused", "temp", "archive"]
            ):
                backup_dirs.append(item)

    return backup_dirs


def analyze_dependencies():
    print("Analyzing dependencies...")

    issues = []

    # Check requirements.txt for potential issues
    req_file = Path("requirements.txt")
    if req_file.exists():
        content = req_file.read_text()
        lines = [
            line.strip()
            for line in content.split("\n")
            if line.strip() and not line.startswith("#")
        ]

        # Look for development-only packages in production requirements
        dev_packages = ["pytest", "coverage", "flake8", "black", "isort", "mypy"]
        found_dev = [pkg for pkg in dev_packages if any(pkg in line for line in lines)]

        if found_dev:
            issues.append(
                f"Development packages in requirements.txt: {', '.join(found_dev)}"
            )

    # Check package.json
    pkg_file = Path("package.json")
    if pkg_file.exists():
        try:
            import json

            with open(pkg_file) as f:
                data = json.load(f)

            deps = data.get("dependencies", {})
            dev_deps = data.get("devDependencies", {})

            # Check for unused testing dependencies in dependencies
            test_packages = ["jest", "playwright", "cypress"]
            for pkg in test_packages:
                if pkg in deps:
                    issues.append(
                        f"Testing package '{pkg}' should be in devDependencies"
                    )

        except:
            issues.append("Could not parse package.json")

    return issues


def check_project_structure():
    print("Checking project structure...")

    structure_issues = []

    # Check for important files
    important_files = [
        ".gitignore",
        "README.md",
        "requirements.txt",
        "manage.py",
        "package.json",
    ]

    for file in important_files:
        if not Path(file).exists():
            structure_issues.append(f"Missing important file: {file}")

    # Check for proper Django structure
    if not Path("portfolio_site").exists():
        structure_issues.append("Django project directory not found")

    if not Path("apps").exists():
        structure_issues.append("Apps directory not found")

    # Check for test directory
    if not Path("tests").exists():
        structure_issues.append("Tests directory not found")

    # Check for static files organization
    static_dir = Path("static")
    if static_dir.exists():
        subdirs = ["css", "js", "images"]
        for subdir in subdirs:
            if not (static_dir / subdir).exists():
                structure_issues.append(f"Missing static subdirectory: {subdir}")

    return structure_issues


def main():
    print("Starting Project Cleanup Audit...")
    print("=" * 50)

    # Find unused files
    unused_files, empty_dirs = find_unused_files()

    print(f"Potentially unused files: {len(unused_files)}")
    if unused_files:
        print("Sample unused files:")
        for file in unused_files[:5]:
            print(f"  {file}")

    print(f"Empty directories: {len(empty_dirs)}")
    if empty_dirs:
        for dir in empty_dirs[:5]:
            print(f"  {dir}")

    # Check for backup directories
    backup_dirs = check_duplicate_files()
    print(f"Backup/old directories: {len(backup_dirs)}")
    if backup_dirs:
        for dir in backup_dirs:
            size = sum(f.stat().st_size for f in dir.rglob("*") if f.is_file()) / (
                1024 * 1024
            )  # MB
            print(f"  {dir} ({size:.1f}MB)")

    # Check dependencies
    dep_issues = analyze_dependencies()
    print(f"Dependency issues: {len(dep_issues)}")
    for issue in dep_issues:
        print(f"  {issue}")

    # Check project structure
    structure_issues = check_project_structure()
    print(f"Structure issues: {len(structure_issues)}")
    for issue in structure_issues:
        print(f"  {issue}")

    # Calculate cleanup score
    cleanup_score = 100

    # Deduct points for issues
    cleanup_score -= len(unused_files) * 2
    cleanup_score -= len(empty_dirs) * 5
    cleanup_score -= len(backup_dirs) * 10
    cleanup_score -= len(dep_issues) * 5
    cleanup_score -= len(structure_issues) * 10

    cleanup_score = max(0, cleanup_score)

    print(f"\n" + "=" * 50)
    print("PROJECT CLEANUP AUDIT RESULTS")
    print("=" * 50)
    print(f"Cleanup Score: {cleanup_score}/100")

    if cleanup_score >= 90:
        print("Status: EXCELLENT - Project is well organized")
    elif cleanup_score >= 70:
        print("Status: GOOD - Minor cleanup needed")
    elif cleanup_score >= 50:
        print("Status: FAIR - Moderate cleanup required")
    else:
        print("Status: NEEDS CLEANUP - Significant cleanup required")

    # Recommendations
    print("\nRecommendations:")

    if unused_files:
        print(f"  - Remove {len(unused_files)} unused files")

    if empty_dirs:
        print(f"  - Remove {len(empty_dirs)} empty directories")

    if backup_dirs:
        print(f"  - Review and clean up {len(backup_dirs)} backup directories")
        total_backup_size = 0
        for dir in backup_dirs:
            size = sum(f.stat().st_size for f in dir.rglob("*") if f.is_file()) / (
                1024 * 1024
            )  # MB
            total_backup_size += size
        print(f"  - Could free up {total_backup_size:.1f}MB of disk space")

    if dep_issues:
        print("  - Clean up dependency configuration")

    if structure_issues:
        print("  - Fix project structure issues")

    if cleanup_score >= 70:
        print("  - Project structure is good for production")
    else:
        print("  - Consider restructuring before production deployment")

    print("\nCleanup audit completed!")

    return cleanup_score >= 60


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
