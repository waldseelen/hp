#!/usr/bin/env python3
"""
Simple UI/UX Audit for Phase 10
"""

import os
import re
from pathlib import Path


def main():
    print("Starting UI/UX Audit...")

    project_root = Path(".")
    templates_dir = project_root / "templates"
    static_dir = project_root / "static"

    # Count files
    html_files = list(templates_dir.rglob("*.html"))
    css_files = list(static_dir.rglob("*.css"))

    print(f"Found {len(html_files)} HTML files")
    print(f"Found {len(css_files)} CSS files")

    # Check for Phase 7 design system usage
    design_system_usage = 0
    total_checks = 0

    # Check HTML files for design system classes
    for html_file in html_files:
        try:
            content = html_file.read_text(encoding="utf-8", errors="ignore")

            # Check for Phase 7 components
            if "btn-primary" in content or "btn-secondary" in content:
                design_system_usage += 1
            total_checks += 1

            if "card-" in content:
                design_system_usage += 1
            total_checks += 1

            if "dark:" in content:
                design_system_usage += 1
            total_checks += 1

        except Exception as e:
            print(f"Error reading {html_file}: {e}")

    # Check CSS files for Phase 7 features
    phase7_features = 0
    css_checks = 0

    for css_file in css_files:
        try:
            content = css_file.read_text(encoding="utf-8", errors="ignore")

            # Check for glassmorphism
            if "backdrop-blur" in content:
                phase7_features += 1
            css_checks += 1

            # Check for brand colors
            if "#e6c547" in content or "#0f172a" in content:
                phase7_features += 1
            css_checks += 1

            # Check for custom properties
            if "--space-" in content:
                phase7_features += 1
            css_checks += 1

        except Exception as e:
            print(f"Error reading {css_file}: {e}")

    # Calculate scores
    design_system_score = (design_system_usage / max(total_checks, 1)) * 100
    phase7_score = (phase7_features / max(css_checks, 1)) * 100

    print("\n" + "=" * 50)
    print("UI/UX AUDIT RESULTS")
    print("=" * 50)
    print(f"Design System Usage: {design_system_score:.1f}%")
    print(f"Phase 7 Features: {phase7_score:.1f}%")

    # Overall consistency score
    overall_score = (design_system_score + phase7_score) / 2
    print(f"Overall Consistency Score: {overall_score:.1f}%")

    if overall_score >= 80:
        print("Status: EXCELLENT - UI/UX is highly consistent")
    elif overall_score >= 60:
        print("Status: GOOD - Minor improvements needed")
    else:
        print("Status: NEEDS IMPROVEMENT - Significant inconsistencies found")

    # Check PWA integration
    base_template = templates_dir / "base.html"
    if base_template.exists():
        try:
            content = base_template.read_text(encoding="utf-8", errors="ignore")
            pwa_score = 0

            if "manifest.json" in content:
                pwa_score += 25
            if "theme-color" in content:
                pwa_score += 25
            if "pwa.min.js" in content:
                pwa_score += 25
            if "apple-mobile-web-app" in content:
                pwa_score += 25

            print(f"PWA Integration Score: {pwa_score}%")

        except Exception as e:
            print(f"Error checking PWA integration: {e}")

    print("\nAudit completed successfully!")
    return overall_score >= 60


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
