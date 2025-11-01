#!/usr/bin/env python3
"""
Performance Audit for Phase 10
"""

import os
import subprocess
from pathlib import Path


def check_file_sizes():
    print("Checking file sizes...")

    static_dir = Path("static")
    large_files = []

    # Check CSS files
    css_files = list(static_dir.rglob("*.css"))
    for css_file in css_files:
        size = css_file.stat().st_size / 1024  # KB
        if size > 100:  # Larger than 100KB
            large_files.append(f"CSS: {css_file} ({size:.1f}KB)")

    # Check JS files
    js_files = list(static_dir.rglob("*.js"))
    for js_file in js_files:
        size = js_file.stat().st_size / 1024  # KB
        if size > 200:  # Larger than 200KB
            large_files.append(f"JS: {js_file} ({size:.1f}KB)")

    # Check image files
    img_extensions = ["*.png", "*.jpg", "*.jpeg", "*.gif", "*.webp", "*.svg"]
    for ext in img_extensions:
        img_files = list(static_dir.rglob(ext))
        for img_file in img_files:
            size = img_file.stat().st_size / 1024  # KB
            if size > 500:  # Larger than 500KB
                large_files.append(f"IMG: {img_file} ({size:.1f}KB)")

    return large_files, len(css_files), len(js_files)


def check_dependencies():
    print("Checking dependencies...")

    # Check Python dependencies
    python_deps = 0
    if Path("requirements.txt").exists():
        with open("requirements.txt", "r") as f:
            lines = f.readlines()
            python_deps = len(
                [line for line in lines if line.strip() and not line.startswith("#")]
            )

    # Check Node dependencies
    node_deps = 0
    if Path("package.json").exists():
        import json

        try:
            with open("package.json", "r") as f:
                data = json.load(f)
                deps = data.get("dependencies", {})
                dev_deps = data.get("devDependencies", {})
                node_deps = len(deps) + len(dev_deps)
        except:
            pass

    return python_deps, node_deps


def check_security_settings():
    print("Checking security settings...")

    security_issues = []

    # Check settings files
    settings_dir = Path("portfolio_site/settings")
    if settings_dir.exists():
        base_settings = settings_dir / "base.py"
        if base_settings.exists():
            try:
                content = base_settings.read_text(encoding="utf-8", errors="ignore")

                # Check for security settings
                if "SECURE_SSL_REDIRECT" not in content:
                    security_issues.append("SECURE_SSL_REDIRECT not configured")

                if "SECURE_HSTS_" not in content:
                    security_issues.append("HSTS headers not configured")

                if "X_FRAME_OPTIONS" not in content:
                    security_issues.append("X-Frame-Options not configured")

                if "SECURE_CONTENT_TYPE_NOSNIFF" not in content:
                    security_issues.append("Content-Type-Nosniff not configured")

            except Exception as e:
                security_issues.append(f"Could not read settings: {e}")

    # Check for environment variables
    env_example = Path(".env.example")
    if not env_example.exists():
        security_issues.append(".env.example file missing")

    return security_issues


def main():
    print("Starting Performance & Security Audit...")
    print("=" * 50)

    # File size analysis
    large_files, css_count, js_count = check_file_sizes()

    print(f"Found {css_count} CSS files")
    print(f"Found {js_count} JS files")

    if large_files:
        print(f"\nLarge files found ({len(large_files)}):")
        for file in large_files[:10]:  # Show first 10
            print(f"  {file}")
    else:
        print("No unusually large files found")

    # Dependencies analysis
    python_deps, node_deps = check_dependencies()
    print(f"\nDependencies:")
    print(f"  Python packages: {python_deps}")
    print(f"  Node packages: {node_deps}")

    # Security check
    security_issues = check_security_settings()
    print(f"\nSecurity Analysis:")
    if security_issues:
        print(f"  Issues found ({len(security_issues)}):")
        for issue in security_issues:
            print(f"    - {issue}")
    else:
        print("  No major security issues found")

    # Performance scoring
    performance_score = 100

    # Deduct points for large files
    if len(large_files) > 5:
        performance_score -= 20
    elif len(large_files) > 2:
        performance_score -= 10

    # Deduct points for too many dependencies
    if python_deps > 30:
        performance_score -= 10
    if node_deps > 50:
        performance_score -= 10

    # Deduct points for security issues
    performance_score -= len(security_issues) * 5

    print(f"\n" + "=" * 50)
    print("PERFORMANCE & SECURITY AUDIT RESULTS")
    print("=" * 50)
    print(f"Performance Score: {max(0, performance_score)}/100")

    if performance_score >= 90:
        print("Status: EXCELLENT - Production ready")
    elif performance_score >= 70:
        print("Status: GOOD - Minor optimizations needed")
    elif performance_score >= 50:
        print("Status: FAIR - Some improvements needed")
    else:
        print("Status: NEEDS WORK - Significant issues found")

    # Recommendations
    print(f"\nRecommendations:")
    if len(large_files) > 2:
        print("  - Optimize large static files")
        print("  - Consider using a CDN for large assets")

    if python_deps > 25:
        print("  - Review Python dependencies for unused packages")

    if node_deps > 40:
        print("  - Review Node dependencies for unused packages")

    if security_issues:
        print("  - Address security configuration issues")
        print("  - Review Django security checklist")

    print("  - Consider running lighthouse audit for detailed performance metrics")
    print("  - Test on slow network connections")

    print("\nAudit completed successfully!")

    return performance_score >= 70


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
