#!/usr/bin/env python3
"""
UI/UX Consistency Audit Script for Phase 10
Audits the entire application for UI/UX consistency across all components
"""

import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple


class UIUXAuditor:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.templates_dir = project_root / "templates"
        self.static_dir = project_root / "static"
        self.css_files = []
        self.html_files = []
        self.js_files = []

        # Phase 7 design system patterns
        self.design_system = {
            "colors": {
                "primary": ["primary-", "text-primary", "bg-primary", "border-primary"],
                "secondary": [
                    "secondary-",
                    "text-secondary",
                    "bg-secondary",
                    "border-secondary",
                ],
                "brand": ["#e6c547", "#0f172a"],  # Brand colors from Phase 7
                "dark_theme": ["dark:", "dark\\:"],
            },
            "typography": {
                "headings": [
                    "heading-1",
                    "heading-2",
                    "heading-3",
                    "text-3xl",
                    "text-2xl",
                    "text-xl",
                ],
                "body": ["body-text", "body-small", "text-base", "text-sm"],
                "font_family": ["font-inter", "Inter", "font-family.*Inter"],
            },
            "spacing": {
                "base_8": [
                    "space-1",
                    "space-2",
                    "space-4",
                    "space-8",
                    "space-16",
                    "space-24",
                ],
                "padding": ["p-1", "p-2", "p-4", "p-8", "px-", "py-"],
                "margin": ["m-1", "m-2", "m-4", "m-8", "mx-", "my-"],
            },
            "components": {
                "buttons": [
                    "btn-primary",
                    "btn-secondary",
                    "btn-tertiary",
                    "btn-danger",
                    "btn-success",
                ],
                "cards": [
                    "card-base",
                    "card-default",
                    "card-glass",
                    "card-premium",
                    "card-interactive",
                ],
                "forms": ["form-base", "form-valid", "form-invalid", "form-control"],
                "navigation": ["nav-container", "nav-link-modern"],
            },
            "effects": {
                "glassmorphism": ["backdrop-blur", "bg-opacity-", "backdrop-filter"],
                "animations": ["animate-", "transition-", "duration-", "ease-"],
                "shadows": ["shadow-", "drop-shadow"],
            },
        }

        self.issues = []
        self.stats = defaultdict(int)

    def scan_files(self):
        """Scan project for all relevant files"""
        print("Scanning project files...")

        # HTML/Template files
        for ext in ["*.html", "*.htm"]:
            self.html_files.extend(self.templates_dir.rglob(ext))

        # CSS files
        for ext in ["*.css"]:
            self.css_files.extend(self.static_dir.rglob(ext))

        # JavaScript files
        for ext in ["*.js"]:
            self.js_files.extend(self.static_dir.rglob(ext))

        print(f"Found {len(self.html_files)} HTML files")
        print(f"Found {len(self.css_files)} CSS files")
        print(f"Found {len(self.js_files)} JS files")

    def audit_color_consistency(self):
        """Audit color usage consistency"""
        print("� Auditing color consistency...")

        color_patterns = {}

        # Check CSS files for color definitions
        for css_file in self.css_files:
            try:
                content = css_file.read_text(encoding="utf-8")

                # Find color definitions
                hex_colors = re.findall(r"#[0-9a-fA-F]{3,6}", content)
                rgb_colors = re.findall(r"rgb\([^)]+\)", content)
                hsl_colors = re.findall(r"hsl\([^)]+\)", content)

                color_patterns[str(css_file)] = {
                    "hex": hex_colors,
                    "rgb": rgb_colors,
                    "hsl": hsl_colors,
                }

                # Check for brand color usage
                brand_color_count = content.count("#e6c547") + content.count("#0f172a")
                self.stats["brand_color_usage"] += brand_color_count

            except Exception as e:
                self.issues.append(f" Could not read CSS file {css_file}: {e}")

        # Check HTML files for inline styles (should be minimal)
        inline_style_count = 0
        for html_file in self.html_files:
            try:
                content = html_file.read_text(encoding="utf-8")
                inline_styles = re.findall(r'style=["\'][^"\']*["\']', content)
                inline_style_count += len(inline_styles)

                if len(inline_styles) > 5:  # Threshold
                    self.issues.append(
                        f"  Excessive inline styles in {html_file} ({len(inline_styles)} found)"
                    )

            except Exception as e:
                self.issues.append(f" Could not read HTML file {html_file}: {e}")

        self.stats["inline_styles"] = inline_style_count

        if inline_style_count > 20:
            self.issues.append(
                "  Too many inline styles found - should use CSS classes instead"
            )

    def audit_typography_consistency(self):
        """Audit typography usage consistency"""
        print("� Auditing typography consistency...")

        typography_usage = defaultdict(int)

        # Check HTML files for typography classes
        for html_file in self.html_files:
            try:
                content = html_file.read_text(encoding="utf-8")

                # Check for design system typography classes
                for category, patterns in self.design_system["typography"].items():
                    for pattern in patterns:
                        matches = len(re.findall(pattern, content))
                        typography_usage[f"{category}_{pattern}"] += matches

                # Check for inconsistent font usage
                font_families = re.findall(r"font-family:[^;]+;", content)
                if font_families:
                    for font in font_families:
                        if "Inter" not in font and "sans-serif" not in font:
                            self.issues.append(
                                f"  Non-standard font found in {html_file}: {font}"
                            )

            except Exception as e:
                self.issues.append(f" Could not read HTML file {html_file}: {e}")

        self.stats["typography_usage"] = dict(typography_usage)

        # Check if design system typography is being used
        if typography_usage["headings_heading-1"] < 1:
            self.issues.append(
                "  Design system heading classes not being used consistently"
            )

    def audit_spacing_consistency(self):
        """Audit spacing and layout consistency"""
        print("� Auditing spacing consistency...")

        spacing_usage = defaultdict(int)

        for html_file in self.html_files:
            try:
                content = html_file.read_text(encoding="utf-8")

                # Check for base-8 spacing system usage
                for category, patterns in self.design_system["spacing"].items():
                    for pattern in patterns:
                        matches = len(re.findall(pattern, content))
                        spacing_usage[f"{category}_{pattern}"] += matches

                # Check for arbitrary values (should be minimal)
                arbitrary_spacing = re.findall(r"[mp][tblrxy]?-\[[^]]+\]", content)
                if len(arbitrary_spacing) > 3:
                    self.issues.append(
                        f"  Too many arbitrary spacing values in {html_file} ({len(arbitrary_spacing)} found)"
                    )

            except Exception as e:
                self.issues.append(f" Could not read HTML file {html_file}: {e}")

        self.stats["spacing_usage"] = dict(spacing_usage)

    def audit_component_consistency(self):
        """Audit component usage consistency"""
        print("� Auditing component consistency...")

        component_usage = defaultdict(int)

        for html_file in self.html_files:
            try:
                content = html_file.read_text(encoding="utf-8")

                # Check for design system component classes
                for category, patterns in self.design_system["components"].items():
                    for pattern in patterns:
                        matches = len(re.findall(pattern, content))
                        component_usage[f"{category}_{pattern}"] += matches

                # Check for button consistency
                button_elements = re.findall(
                    r'<button[^>]*class=["\'][^"\']*["\'][^>]*>', content
                )
                for button in button_elements:
                    if not any(
                        btn_class in button
                        for btn_class in self.design_system["components"]["buttons"]
                    ):
                        if "btn-" not in button:  # Should use design system
                            self.issues.append(
                                f"  Button without design system class in {html_file}"
                            )

            except Exception as e:
                self.issues.append(f" Could not read HTML file {html_file}: {e}")

        self.stats["component_usage"] = dict(component_usage)

    def audit_dark_theme_consistency(self):
        """Audit dark theme implementation consistency"""
        print("� Auditing dark theme consistency...")

        dark_theme_usage = defaultdict(int)
        missing_dark_variants = []

        for html_file in self.html_files:
            try:
                content = html_file.read_text(encoding="utf-8")

                # Count dark: variant usage
                dark_variants = re.findall(r"dark:[a-zA-Z0-9-]+", content)
                dark_theme_usage[str(html_file)] = len(dark_variants)

                # Check for light colors without dark variants
                light_bg_classes = re.findall(
                    r"bg-white|bg-gray-50|bg-gray-100", content
                )
                for light_class in light_bg_classes:
                    if (
                        f"dark:{light_class.replace('white', 'gray-900').replace('50', '800').replace('100', '700')}"
                        not in content
                    ):
                        missing_dark_variants.append(f"{html_file}: {light_class}")

            except Exception as e:
                self.issues.append(f" Could not read HTML file {html_file}: {e}")

        self.stats["dark_theme_usage"] = dict(dark_theme_usage)

        if missing_dark_variants:
            for missing in missing_dark_variants[:5]:  # Show first 5
                self.issues.append(f"  Missing dark theme variant: {missing}")

    def audit_animation_performance(self):
        """Audit animation and performance consistency"""
        print(" Auditing animation performance...")

        animation_usage = defaultdict(int)

        for html_file in self.html_files:
            try:
                content = html_file.read_text(encoding="utf-8")

                # Check for Phase 7 animation classes
                for category, patterns in self.design_system["effects"].items():
                    for pattern in patterns:
                        matches = len(re.findall(pattern, content))
                        animation_usage[f"{category}_{pattern}"] += matches

                # Check for prefers-reduced-motion support
                if "motion-reduce:" not in content and (
                    "animate-" in content or "transition-" in content
                ):
                    motion_classes = len(re.findall(r"animate-|transition-", content))
                    if motion_classes > 3:
                        self.issues.append(
                            f"  Missing motion-reduce variants in {html_file} (has {motion_classes} animations)"
                        )

            except Exception as e:
                self.issues.append(f" Could not read HTML file {html_file}: {e}")

        self.stats["animation_usage"] = dict(animation_usage)

    def audit_pwa_integration(self):
        """Audit PWA integration consistency"""
        print("� Auditing PWA integration...")

        # Check base template for PWA meta tags
        base_template = self.templates_dir / "base.html"
        if base_template.exists():
            try:
                content = base_template.read_text(encoding="utf-8")

                required_pwa_elements = [
                    "manifest.json",
                    "theme-color",
                    "apple-mobile-web-app",
                    "pwa.min.js",
                ]

                for element in required_pwa_elements:
                    if element not in content:
                        self.issues.append(
                            f"  Missing PWA element in base template: {element}"
                        )
                    else:
                        self.stats["pwa_elements_found"] += 1

            except Exception as e:
                self.issues.append(f" Could not read base template: {e}")
        else:
            self.issues.append(" Base template not found")

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive audit report"""
        print("� Generating audit report...")

        total_issues = len(self.issues)
        critical_issues = len([issue for issue in self.issues if "" in issue])
        warnings = len([issue for issue in self.issues if "" in issue])

        # Calculate consistency score
        consistency_score = max(0, 100 - (critical_issues * 10) - (warnings * 5))

        report = {
            "audit_summary": {
                "total_files_scanned": len(self.html_files)
                + len(self.css_files)
                + len(self.js_files),
                "total_issues": total_issues,
                "critical_issues": critical_issues,
                "warnings": warnings,
                "consistency_score": consistency_score,
                "status": "PASS" if consistency_score >= 80 else "NEEDS_IMPROVEMENT",
            },
            "statistics": dict(self.stats),
            "issues": self.issues,
            "recommendations": self.generate_recommendations(),
            "design_system_coverage": self.calculate_design_system_coverage(),
        }

        return report

    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on audit findings"""
        recommendations = []

        if self.stats.get("inline_styles", 0) > 20:
            recommendations.append("� Reduce inline styles and move to CSS classes")

        if self.stats.get("brand_color_usage", 0) < 10:
            recommendations.append(
                "� Increase usage of brand colors throughout the application"
            )

        if len([issue for issue in self.issues if "dark theme" in issue]) > 3:
            recommendations.append(
                "� Improve dark theme consistency across all components"
            )

        if len([issue for issue in self.issues if "Button without" in issue]) > 0:
            recommendations.append(
                "� Apply design system button classes to all button elements"
            )

        if len([issue for issue in self.issues if "motion-reduce" in issue]) > 0:
            recommendations.append(
                " Add motion-reduce variants for better accessibility"
            )

        return recommendations

    def calculate_design_system_coverage(self) -> Dict[str, float]:
        """Calculate how much of the design system is being used"""
        coverage = {}

        for category in self.design_system:
            total_patterns = sum(
                len(patterns) for patterns in self.design_system[category].values()
            )
            used_patterns = len(
                [
                    k
                    for k in self.stats.get(f"{category}_usage", {})
                    if self.stats.get(f"{category}_usage", {}).get(k, 0) > 0
                ]
            )
            coverage[category] = (
                (used_patterns / total_patterns * 100) if total_patterns > 0 else 0
            )

        return coverage


def main():
    """Run the UI/UX audit"""
    project_root = Path(__file__).parent.parent
    auditor = UIUXAuditor(project_root)

    print("Starting UI/UX Consistency Audit for Phase 10...")
    print("=" * 60)

    # Run audit steps
    auditor.scan_files()
    auditor.audit_color_consistency()
    auditor.audit_typography_consistency()
    auditor.audit_spacing_consistency()
    auditor.audit_component_consistency()
    auditor.audit_dark_theme_consistency()
    auditor.audit_animation_performance()
    auditor.audit_pwa_integration()

    # Generate and save report
    report = auditor.generate_report()

    # Save report to file
    report_file = project_root / "ui_ux_audit_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Print summary
    print("\n" + "=" * 60)
    print("UI/UX AUDIT RESULTS")
    print("=" * 60)
    print(f"Files Scanned: {report['audit_summary']['total_files_scanned']}")
    print(f"Consistency Score: {report['audit_summary']['consistency_score']}/100")
    print(f"Critical Issues: {report['audit_summary']['critical_issues']}")
    print(f"Warnings: {report['audit_summary']['warnings']}")
    print(f"Status: {report['audit_summary']['status']}")

    print(f"\n� Design System Coverage:")
    for category, coverage in report["design_system_coverage"].items():
        print(f"  {category.title()}: {coverage:.1f}%")

    if report["issues"]:
        print(f"\n� Top Issues:")
        for issue in report["issues"][:10]:  # Show top 10
            print(f"  {issue}")

    if report["recommendations"]:
        print(f"\n� Recommendations:")
        for rec in report["recommendations"]:
            print(f"  {rec}")

    print(f"\n� Full report saved to: {report_file}")

    return report["audit_summary"]["status"] == "PASS"


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
