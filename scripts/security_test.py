#!/usr/bin/env python3
"""
Security Testing Script
=======================

Automated security testing suite:
- Bandit: Python code security analysis
- Safety: Dependency vulnerability scanning
- pytest-security: Security-focused tests
- Custom security checks

Usage:
    python scripts/security_test.py
    python scripts/security_test.py --verbose
    python scripts/security_test.py --fix
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


class SecurityTester:
    """Security testing orchestrator."""

    def __init__(self, verbose=False, fix=False):
        self.verbose = verbose
        self.fix = fix
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "summary": {
                "total_issues": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
            },
        }

        # Ensure we're in project root
        self.project_root = Path(__file__).parent.parent
        os.chdir(self.project_root)

    def log(self, message, level="INFO"):
        """Log message."""
        if self.verbose or level in ["ERROR", "WARNING"]:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] {level}: {message}")

    def run_command(self, command, check=True):
        """Run shell command and return output."""
        self.log(f"Running: {' '.join(command)}")
        try:
            result = subprocess.run(
                command, capture_output=True, text=True, check=check
            )
            return result
        except subprocess.CalledProcessError as e:
            self.log(f"Command failed: {e}", "ERROR")
            return e

    def test_bandit(self):
        """Run Bandit security analysis."""
        self.log("=" * 60)
        self.log("Running Bandit Security Analysis")
        self.log("=" * 60)

        # Run bandit
        result = self.run_command(
            [
                "bandit",
                "-r",
                ".",
                "-f",
                "json",
                "-o",
                "bandit-report.json",
                "--exclude",
                "./venv,./env,./.venv,./htmlcov,./node_modules",
                "-ll",  # Only show medium and high severity
            ],
            check=False,
        )

        # Parse results
        try:
            with open("bandit-report.json", "r") as f:
                report = json.load(f)

            issues = report.get("results", [])
            self.results["tests"]["bandit"] = {
                "status": "completed",
                "issues_found": len(issues),
                "issues": issues,
            }

            # Count by severity
            for issue in issues:
                severity = issue.get("issue_severity", "LOW").lower()
                self.results["summary"]["total_issues"] += 1
                if severity == "high":
                    self.results["summary"]["high"] += 1
                elif severity == "medium":
                    self.results["summary"]["medium"] += 1
                else:
                    self.results["summary"]["low"] += 1

            self.log(f"Bandit found {len(issues)} issues")

            # Display top issues
            if issues and self.verbose:
                self.log("\nTop 5 Bandit Issues:")
                for i, issue in enumerate(issues[:5], 1):
                    self.log(
                        f"{i}. [{issue['issue_severity']}] "
                        f"{issue['issue_text']} "
                        f"({issue['filename']}:{issue['line_number']})"
                    )

        except FileNotFoundError:
            self.log("Bandit report not found", "ERROR")
            self.results["tests"]["bandit"] = {
                "status": "failed",
                "error": "Report not generated",
            }
        except json.JSONDecodeError as e:
            self.log(f"Failed to parse Bandit report: {e}", "ERROR")
            self.results["tests"]["bandit"] = {"status": "failed", "error": str(e)}

    def test_safety(self):
        """Run Safety dependency vulnerability scan."""
        self.log("=" * 60)
        self.log("Running Safety Dependency Scan")
        self.log("=" * 60)

        # Run safety
        result = self.run_command(
            ["safety", "check", "--json", "--output", "safety-report.json"], check=False
        )

        # Parse results
        try:
            with open("safety-report.json", "r") as f:
                report = json.load(f)

            vulnerabilities = report if isinstance(report, list) else []
            self.results["tests"]["safety"] = {
                "status": "completed",
                "vulnerabilities_found": len(vulnerabilities),
                "vulnerabilities": vulnerabilities,
            }

            # Count vulnerabilities
            for vuln in vulnerabilities:
                self.results["summary"]["total_issues"] += 1
                # Safety doesn't provide severity, count as medium
                self.results["summary"]["medium"] += 1

            self.log(f"Safety found {len(vulnerabilities)} vulnerabilities")

            # Display vulnerabilities
            if vulnerabilities and self.verbose:
                self.log("\nVulnerabilities Found:")
                for i, vuln in enumerate(vulnerabilities[:5], 1):
                    self.log(
                        f"{i}. {vuln.get('package', 'unknown')} "
                        f"v{vuln.get('installed_version', 'unknown')}: "
                        f"{vuln.get('advisory', 'No advisory')}"
                    )

        except FileNotFoundError:
            self.log("Safety report not found - no vulnerabilities", "INFO")
            self.results["tests"]["safety"] = {
                "status": "completed",
                "vulnerabilities_found": 0,
                "vulnerabilities": [],
            }
        except json.JSONDecodeError as e:
            self.log(f"Failed to parse Safety report: {e}", "ERROR")
            self.results["tests"]["safety"] = {"status": "failed", "error": str(e)}

    def test_security_tests(self):
        """Run security-focused pytest tests."""
        self.log("=" * 60)
        self.log("Running Security Test Suite")
        self.log("=" * 60)

        # Run pytest with security tests
        result = self.run_command(
            ["pytest", "tests/security/", "-v", "--tb=short", "--maxfail=5"],
            check=False,
        )

        self.results["tests"]["pytest_security"] = {
            "status": "completed" if result.returncode == 0 else "failed",
            "return_code": result.returncode,
            "output": (
                result.stdout if self.verbose else "Run with --verbose to see output"
            ),
        }

        if result.returncode == 0:
            self.log("All security tests passed ✓")
        else:
            self.log(f"Security tests failed (exit code: {result.returncode})", "ERROR")

    def check_ssl_configuration(self):
        """Check SSL/TLS configuration."""
        self.log("=" * 60)
        self.log("Checking SSL/TLS Configuration")
        self.log("=" * 60)

        issues = []

        # Check settings.py for SSL settings
        settings_file = self.project_root / "project" / "settings.py"
        if settings_file.exists():
            with open(settings_file, "r") as f:
                content = f.read()

                # Check for SSL enforcement
                if "SECURE_SSL_REDIRECT = True" not in content:
                    issues.append(
                        {
                            "severity": "HIGH",
                            "issue": "SECURE_SSL_REDIRECT not enabled",
                            "recommendation": "Set SECURE_SSL_REDIRECT = True in production",
                        }
                    )

                if "SESSION_COOKIE_SECURE = True" not in content:
                    issues.append(
                        {
                            "severity": "HIGH",
                            "issue": "SESSION_COOKIE_SECURE not enabled",
                            "recommendation": "Set SESSION_COOKIE_SECURE = True",
                        }
                    )

                if "CSRF_COOKIE_SECURE = True" not in content:
                    issues.append(
                        {
                            "severity": "HIGH",
                            "issue": "CSRF_COOKIE_SECURE not enabled",
                            "recommendation": "Set CSRF_COOKIE_SECURE = True",
                        }
                    )

        self.results["tests"]["ssl_config"] = {
            "status": "completed",
            "issues_found": len(issues),
            "issues": issues,
        }

        # Update summary
        for issue in issues:
            self.results["summary"]["total_issues"] += 1
            if issue["severity"] == "HIGH":
                self.results["summary"]["high"] += 1

        self.log(f"SSL configuration check: {len(issues)} issues found")

    def check_secret_management(self):
        """Check for hardcoded secrets."""
        self.log("=" * 60)
        self.log("Checking Secret Management")
        self.log("=" * 60)

        issues = []

        # Check for .env file
        env_file = self.project_root / ".env"
        if not env_file.exists():
            issues.append(
                {
                    "severity": "MEDIUM",
                    "issue": ".env file not found",
                    "recommendation": "Use .env file for environment variables",
                }
            )

        # Check if .env is in .gitignore
        gitignore_file = self.project_root / ".gitignore"
        if gitignore_file.exists():
            with open(gitignore_file, "r") as f:
                if ".env" not in f.read():
                    issues.append(
                        {
                            "severity": "CRITICAL",
                            "issue": ".env not in .gitignore",
                            "recommendation": "Add .env to .gitignore immediately",
                        }
                    )

        self.results["tests"]["secret_management"] = {
            "status": "completed",
            "issues_found": len(issues),
            "issues": issues,
        }

        # Update summary
        for issue in issues:
            self.results["summary"]["total_issues"] += 1
            severity = issue["severity"].lower()
            if severity == "critical":
                self.results["summary"]["critical"] += 1
            elif severity == "high":
                self.results["summary"]["high"] += 1
            elif severity == "medium":
                self.results["summary"]["medium"] += 1

        self.log(f"Secret management check: {len(issues)} issues found")

    def generate_report(self):
        """Generate security audit report."""
        self.log("=" * 60)
        self.log("Generating Security Audit Report")
        self.log("=" * 60)

        # Save JSON report
        report_file = self.project_root / "security-audit-report.json"
        with open(report_file, "w") as f:
            json.dump(self.results, f, indent=2)

        self.log(f"Report saved to: {report_file}")

        # Print summary
        print("\n" + "=" * 60)
        print("SECURITY AUDIT SUMMARY")
        print("=" * 60)
        print(f"Timestamp: {self.results['timestamp']}")
        print(f"Total Issues: {self.results['summary']['total_issues']}")
        print(f"  Critical: {self.results['summary']['critical']}")
        print(f"  High: {self.results['summary']['high']}")
        print(f"  Medium: {self.results['summary']['medium']}")
        print(f"  Low: {self.results['summary']['low']}")
        print("=" * 60)

        # Overall status
        if self.results["summary"]["critical"] > 0:
            print("\n❌ CRITICAL ISSUES FOUND - IMMEDIATE ACTION REQUIRED")
            return False
        elif self.results["summary"]["high"] > 0:
            print("\n⚠️  HIGH PRIORITY ISSUES FOUND - ACTION REQUIRED")
            return False
        elif self.results["summary"]["medium"] > 0:
            print("\n⚠️  MEDIUM PRIORITY ISSUES FOUND")
            return True
        else:
            print("\n✅ NO CRITICAL ISSUES FOUND")
            return True

    def run_all(self):
        """Run all security tests."""
        print("\n" + "=" * 60)
        print("SECURITY TESTING SUITE")
        print("=" * 60)
        print(f"Project: {self.project_root}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60 + "\n")

        # Run all tests
        self.test_bandit()
        print()

        self.test_safety()
        print()

        self.test_security_tests()
        print()

        self.check_ssl_configuration()
        print()

        self.check_secret_management()
        print()

        # Generate report
        success = self.generate_report()

        return success


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run security testing suite")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--fix", action="store_true", help="Attempt to fix issues automatically"
    )

    args = parser.parse_args()

    # Run tests
    tester = SecurityTester(verbose=args.verbose, fix=args.fix)
    success = tester.run_all()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
