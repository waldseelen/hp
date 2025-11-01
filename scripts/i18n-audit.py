#!/usr/bin/env python3
"""
COMPREHENSIVE I18N AUDIT SCRIPT
Analyzes translation coverage and identifies missing translations
"""

import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path


class I18nAuditor:
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.templates_dir = self.project_root / "templates"
        self.locale_dir = self.project_root / "locale"
        self.static_dir = self.project_root / "static"

        self.issues = {
            "missing_trans_tags": [],
            "hardcoded_strings": [],
            "missing_translations": [],
            "inconsistent_translations": [],
            "js_translations": [],
            "po_file_issues": [],
        }

        self.translation_keys = set()
        self.hardcoded_patterns = [
            r'["\']([A-ZÜĞIŞÖÇ][a-züğışçöü\s]{3,})["\']',  # Turkish text
            r'["\']([A-Z][a-z\s]{3,})["\']',  # English text
            r">([A-ZÜĞIŞÖÇ][a-züğışçöü\s]{3,})<",  # HTML content
            r">([A-Z][a-z\s]{3,})<",  # HTML content English
        ]

    def run_audit(self):
        """Run complete i18n audit"""
        print("Starting Comprehensive I18N Audit...")

        # Analyze templates
        self.analyze_templates()

        # Analyze JavaScript files
        self.analyze_javascript()

        # Analyze .po files
        self.analyze_po_files()

        # Check for missing translations
        self.check_missing_translations()

        # Generate report
        report = self.generate_report()

        return report

    def analyze_templates(self):
        """Analyze Django templates for i18n issues"""
        print("Analyzing templates...")

        for template_file in self.templates_dir.rglob("*.html"):
            try:
                with open(template_file, "r", encoding="utf-8") as f:
                    content = f.read()

                self._check_template_i18n(template_file, content)

            except Exception as e:
                print(f"Error analyzing {template_file}: {e}")

    def _check_template_i18n(self, template_file, content):
        """Check individual template for i18n issues"""
        relative_path = template_file.relative_to(self.project_root)

        # Check if {% load i18n %} is present but no translations used
        has_i18n_load = "{% load i18n %}" in content
        has_trans_usage = bool(re.search(r"{%\s*trans\s+", content))

        if has_i18n_load and not has_trans_usage:
            self.issues["missing_trans_tags"].append(
                {
                    "file": str(relative_path),
                    "issue": "Has i18n load but no trans usage",
                    "line": self._get_line_number(content, "{% load i18n %}"),
                }
            )

        # Find hardcoded strings that should be translated
        for pattern in self.hardcoded_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                text = match.group(1).strip()
                if len(text) > 3 and self._should_be_translated(text):
                    line_num = self._get_line_number(content, match.group(0))
                    self.issues["hardcoded_strings"].append(
                        {
                            "file": str(relative_path),
                            "text": text,
                            "line": line_num,
                            "context": match.group(0),
                        }
                    )

        # Extract existing trans keys
        trans_matches = re.finditer(r'{%\s*trans\s+["\']([^"\']+)["\']', content)
        for match in trans_matches:
            self.translation_keys.add(match.group(1))

    def analyze_javascript(self):
        """Analyze JavaScript files for untranslated strings"""
        print("Analyzing JavaScript files...")

        js_files = list(self.static_dir.rglob("*.js"))

        for js_file in js_files:
            try:
                with open(js_file, "r", encoding="utf-8") as f:
                    content = f.read()

                self._check_js_strings(js_file, content)

            except Exception as e:
                print(f"Error analyzing {js_file}: {e}")

    def _check_js_strings(self, js_file, content):
        """Check JavaScript file for translatable strings"""
        relative_path = js_file.relative_to(self.project_root)

        # Find console.log, alert, confirm, etc. with Turkish/English text
        js_string_patterns = [
            r'console\.log\(["\']([^"\']{4,})["\']',
            r'alert\(["\']([^"\']{4,})["\']',
            r'confirm\(["\']([^"\']{4,})["\']',
            r'["\']([A-ZÜĞIŞÖÇ][a-züğışçöü\s]{4,})["\']',
            r'innerHTML\s*=\s*["\']([^"\']{4,})["\']',
        ]

        for pattern in js_string_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                text = match.group(1).strip()
                if self._should_be_translated(text):
                    line_num = self._get_line_number(content, match.group(0))
                    self.issues["js_translations"].append(
                        {
                            "file": str(relative_path),
                            "text": text,
                            "line": line_num,
                            "suggestion": f'gettext("{text}")',
                        }
                    )

    def analyze_po_files(self):
        """Analyze .po files for issues"""
        print("Analyzing .po files...")

        for lang_dir in self.locale_dir.iterdir():
            if lang_dir.is_dir():
                po_file = lang_dir / "LC_MESSAGES" / "django.po"
                if po_file.exists():
                    self._check_po_file(po_file, lang_dir.name)

    def _check_po_file(self, po_file, language):
        """Check individual .po file for issues"""
        try:
            with open(po_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Check for fuzzy translations
            fuzzy_count = content.count("#, fuzzy")
            if fuzzy_count > 0:
                self.issues["po_file_issues"].append(
                    {
                        "file": f"locale/{language}/LC_MESSAGES/django.po",
                        "issue": f"{fuzzy_count} fuzzy translations need review",
                    }
                )

            # Check for empty translations
            empty_msgstr = re.findall(r'msgid "([^"]+)"\nmsgstr ""', content)
            if empty_msgstr:
                self.issues["po_file_issues"].append(
                    {
                        "file": f"locale/{language}/LC_MESSAGES/django.po",
                        "issue": f"{len(empty_msgstr)} empty translations",
                        "examples": empty_msgstr[:5],
                    }
                )

            # Extract translation keys
            msgid_pattern = r'msgid "([^"]+)"'
            msgids = re.findall(msgid_pattern, content)

            return set(msgids)

        except Exception as e:
            self.issues["po_file_issues"].append(
                {
                    "file": f"locale/{language}/LC_MESSAGES/django.po",
                    "issue": f"Error reading file: {e}",
                }
            )
            return set()

    def check_missing_translations(self):
        """Check for missing translations between languages"""
        print("Checking for missing translations...")

        tr_keys = set()
        en_keys = set()

        # Get keys from both language files
        tr_po = self.locale_dir / "tr" / "LC_MESSAGES" / "django.po"
        en_po = self.locale_dir / "en" / "LC_MESSAGES" / "django.po"

        if tr_po.exists():
            tr_keys = self._check_po_file(tr_po, "tr") or set()

        if en_po.exists():
            en_keys = self._check_po_file(en_po, "en") or set()

        # Find missing translations
        missing_in_tr = en_keys - tr_keys
        missing_in_en = tr_keys - en_keys

        if missing_in_tr:
            self.issues["missing_translations"].append(
                {
                    "language": "Turkish",
                    "missing_keys": list(missing_in_tr)[:10],  # Show first 10
                    "total_missing": len(missing_in_tr),
                }
            )

        if missing_in_en:
            self.issues["missing_translations"].append(
                {
                    "language": "English",
                    "missing_keys": list(missing_in_en)[:10],
                    "total_missing": len(missing_in_en),
                }
            )

    def _should_be_translated(self, text):
        """Determine if text should be translated"""
        # Skip technical terms, URLs, etc.
        skip_patterns = [
            r"^https?://",  # URLs
            r"^\w+\.\w+",  # file extensions
            r"^\d+$",  # numbers only
            r"^[A-Z_]+$",  # constants
            r"^#[0-9a-fA-F]+$",  # hex colors
        ]

        for pattern in skip_patterns:
            if re.match(pattern, text):
                return False

        return True

    def _get_line_number(self, content, search_text):
        """Get line number for text in content"""
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            if search_text in line:
                return i
        return 0

    def generate_report(self):
        """Generate comprehensive audit report"""
        print("Generating audit report...")

        report = {
            "summary": {
                "total_issues": sum(len(issues) for issues in self.issues.values()),
                "hardcoded_strings": len(self.issues["hardcoded_strings"]),
                "js_translations_needed": len(self.issues["js_translations"]),
                "po_file_issues": len(self.issues["po_file_issues"]),
                "missing_translations": sum(
                    item.get("total_missing", 0)
                    for item in self.issues["missing_translations"]
                ),
            },
            "issues": self.issues,
            "recommendations": self._generate_recommendations(),
        }

        # Save report
        report_file = self.project_root / "I18N_AUDIT_REPORT.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        # Generate readable report
        self._generate_readable_report(report)

        return report

    def _generate_recommendations(self):
        """Generate actionable recommendations"""
        recommendations = []

        if self.issues["hardcoded_strings"]:
            recommendations.append(
                {
                    "priority": "high",
                    "action": "Replace hardcoded strings with {% trans %} tags",
                    "files_affected": len(
                        set(item["file"] for item in self.issues["hardcoded_strings"])
                    ),
                }
            )

        if self.issues["js_translations"]:
            recommendations.append(
                {
                    "priority": "medium",
                    "action": "Implement JavaScript i18n system",
                    "details": "Add gettext support for JavaScript strings",
                }
            )

        if self.issues["po_file_issues"]:
            recommendations.append(
                {
                    "priority": "medium",
                    "action": "Update and compile .po files",
                    "command": "python manage.py makemessages && python manage.py compilemessages",
                }
            )

        return recommendations

    def _generate_readable_report(self, report):
        """Generate human-readable report"""
        report_md = self.project_root / "I18N_AUDIT_REPORT.md"

        with open(report_md, "w", encoding="utf-8") as f:
            f.write("# I18N Audit Report\n\n")

            # Summary
            f.write("## Summary\n\n")
            summary = report["summary"]
            f.write(f"- **Total Issues**: {summary['total_issues']}\n")
            f.write(f"- **Hardcoded Strings**: {summary['hardcoded_strings']}\n")
            f.write(
                f"- **JS Translations Needed**: {summary['js_translations_needed']}\n"
            )
            f.write(f"- **PO File Issues**: {summary['po_file_issues']}\n")
            f.write(
                f"- **Missing Translations**: {summary['missing_translations']}\n\n"
            )

            # Hardcoded strings
            if self.issues["hardcoded_strings"]:
                f.write("## Hardcoded Strings\n\n")
                for item in self.issues["hardcoded_strings"][:20]:
                    f.write(f"**{item['file']}:{item['line']}**\n")
                    f.write(f"```\n{item['context']}\n```\n")
                    f.write(f"Text: `{item['text']}`\n\n")

            # JavaScript translations
            if self.issues["js_translations"]:
                f.write("## JavaScript Translations Needed\n\n")
                for item in self.issues["js_translations"][:10]:
                    f.write(f"**{item['file']}:{item['line']}**\n")
                    f.write(f"Text: `{item['text']}`\n")
                    f.write(f"Suggestion: `{item['suggestion']}`\n\n")

            # Recommendations
            f.write("## Recommendations\n\n")
            for rec in report["recommendations"]:
                f.write(f"### {rec['priority'].upper()} Priority\n")
                f.write(f"{rec['action']}\n\n")
                if "command" in rec:
                    f.write(f"```bash\n{rec['command']}\n```\n\n")


def main():
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = os.getcwd()

    auditor = I18nAuditor(project_root)
    report = auditor.run_audit()

    print(f"\nAudit complete! Found {report['summary']['total_issues']} issues.")
    print("Check I18N_AUDIT_REPORT.md for detailed results.")


if __name__ == "__main__":
    main()
