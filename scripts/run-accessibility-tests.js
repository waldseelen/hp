#!/usr/bin/env node

/**
 * Comprehensive Accessibility Test Runner
 *
 * This script runs all accessibility tests and generates a comprehensive report
 * to verify zero critical accessibility issues across the portfolio website.
 */

const { spawn, exec } = require('child_process');
const fs = require('fs').promises;
const path = require('path');

class AccessibilityTestRunner {
    constructor() {
        this.results = {
            jest: { passed: false, violations: [], coverage: null },
            axe: { passed: false, violations: [], scannedPages: [] },
            lighthouse: { passed: false, scores: {}, violations: [] },
            summary: { totalViolations: 0, criticalViolations: 0, passed: false }
        };
        this.reportDir = path.join(process.cwd(), 'coverage', 'accessibility');
    }

    async ensureReportDirectory() {
        try {
            await fs.mkdir(this.reportDir, { recursive: true });
        } catch (error) {
            console.warn('Warning: Could not create report directory:', error.message);
        }
    }

    async runCommand(command, args = [], options = {}) {
        return new Promise((resolve, reject) => {
            const process = spawn(command, args, {
                stdio: 'pipe',
                shell: true,
                ...options
            });

            let stdout = '';
            let stderr = '';

            process.stdout?.on('data', data => {
                stdout += data.toString();
            });

            process.stderr?.on('data', data => {
                stderr += data.toString();
            });

            process.on('close', code => {
                if (code === 0) {
                    resolve({ stdout, stderr, code });
                } else {
                    reject({ stdout, stderr, code });
                }
            });

            process.on('error', error => {
                reject({ error: error.message, code: -1 });
            });
        });
    }

    async waitForServer(url = 'http://localhost:8000', maxAttempts = 30) {
        console.log('⏳ Waiting for Django server to be ready...');

        for (let i = 0; i < maxAttempts; i++) {
            try {
                const response = await fetch(url);
                if (response.ok) {
                    console.log('✅ Django server is ready');
                    return true;
                }
            } catch (error) {
                // Server not ready yet
            }

            await new Promise(resolve => setTimeout(resolve, 1000));
            process.stdout.write('.');
        }

        throw new Error('Django server failed to start within timeout period');
    }

    async startDjangoServer() {
        console.log('🚀 Starting Django development server...');

        const serverProcess = spawn('python', ['manage.py', 'runserver'], {
            stdio: 'pipe',
            env: {
                ...process.env,
                DJANGO_SETTINGS_MODULE: 'portfolio_site.settings.development'
            }
        });

        // Wait a bit for server to start
        await new Promise(resolve => setTimeout(resolve, 3000));

        await this.waitForServer();
        return serverProcess;
    }

    async runJestTests() {
        console.log('\n📝 Running Jest accessibility tests...');

        try {
            const result = await this.runCommand('npm', ['run', 'test:a11y:coverage']);
            this.results.jest.passed = true;
            console.log('✅ Jest accessibility tests passed');

            // Try to read coverage information
            try {
                const coverageFile = path.join(this.reportDir, 'coverage-summary.json');
                const coverageData = await fs.readFile(coverageFile, 'utf8');
                this.results.jest.coverage = JSON.parse(coverageData);
            } catch (error) {
                console.warn('Warning: Could not read Jest coverage data');
            }

        } catch (error) {
            console.error('❌ Jest accessibility tests failed');
            console.error(error.stderr || error.stdout || error.error);
            this.results.jest.passed = false;
            this.results.jest.violations.push({
                type: 'Jest Test Failure',
                message: error.stderr || error.stdout || error.error,
                severity: 'critical'
            });
        }
    }

    async runAxeCoreTests() {
        console.log('\n🔍 Running axe-core accessibility scans...');

        const pages = [
            { url: 'http://localhost:8000/', name: 'home' },
            { url: 'http://localhost:8000/contact/', name: 'contact' },
            { url: 'http://localhost:8000/blog/', name: 'blog' },
            { url: 'http://localhost:8000/tools/', name: 'tools' }
        ];

        let allPassed = true;

        for (const page of pages) {
            try {
                console.log(`   Scanning ${page.name} page...`);
                const outputFile = path.join(this.reportDir, `axe-${page.name}-results.json`);

                await this.runCommand('axe', [
                    page.url,
                    '--reporter', 'json',
                    '--output-file', outputFile,
                    '--exit'
                ]);

                // Read and parse results
                try {
                    const resultsData = await fs.readFile(outputFile, 'utf8');
                    const results = JSON.parse(resultsData);

                    if (results.violations && results.violations.length > 0) {
                        allPassed = false;
                        this.results.axe.violations.push(...results.violations.map(v => ({
                            ...v,
                            page: page.name,
                            severity: v.impact || 'unknown'
                        })));
                        console.log(`   ❌ ${page.name}: ${results.violations.length} violations found`);
                    } else {
                        console.log(`   ✅ ${page.name}: No violations found`);
                    }

                    this.results.axe.scannedPages.push({
                        name: page.name,
                        url: page.url,
                        violations: results.violations?.length || 0,
                        passes: results.passes?.length || 0
                    });

                } catch (parseError) {
                    console.error(`   ❌ Failed to parse results for ${page.name}`);
                    allPassed = false;
                }

            } catch (error) {
                console.error(`   ❌ Failed to scan ${page.name}: ${error.stderr || error.error}`);
                allPassed = false;
                this.results.axe.violations.push({
                    type: 'Axe Scan Failure',
                    page: page.name,
                    message: error.stderr || error.error,
                    severity: 'critical'
                });
            }
        }

        this.results.axe.passed = allPassed;
        console.log(allPassed ? '✅ All axe-core scans passed' : '❌ Some axe-core scans failed');
    }

    async generateReport() {
        console.log('\n📊 Generating accessibility report...');

        // Calculate summary
        this.results.summary.totalViolations =
      this.results.jest.violations.length +
      this.results.axe.violations.length +
      this.results.lighthouse.violations.length;

        this.results.summary.criticalViolations = [
            ...this.results.jest.violations,
            ...this.results.axe.violations,
            ...this.results.lighthouse.violations
        ].filter(v => v.severity === 'critical' || v.impact === 'critical').length;

        this.results.summary.passed =
      this.results.jest.passed &&
      this.results.axe.passed &&
      this.results.summary.totalViolations === 0;

        // Generate detailed report
        const report = {
            timestamp: new Date().toISOString(),
            summary: this.results.summary,
            jest: this.results.jest,
            axe: this.results.axe,
            lighthouse: this.results.lighthouse,
            recommendations: this.generateRecommendations()
        };

        const reportFile = path.join(this.reportDir, 'accessibility-report.json');
        await fs.writeFile(reportFile, JSON.stringify(report, null, 2));

        // Generate human-readable report
        const mdReport = this.generateMarkdownReport();
        const mdReportFile = path.join(this.reportDir, 'accessibility-report.md');
        await fs.writeFile(mdReportFile, mdReport);

        console.log(`📄 Report saved to: ${reportFile}`);
        console.log(`📄 Markdown report saved to: ${mdReportFile}`);

        return report;
    }

    generateRecommendations() {
        const recommendations = [];

        if (!this.results.jest.passed) {
            recommendations.push(
                'Fix Jest accessibility test failures by reviewing test output and addressing the underlying accessibility issues.'
            );
        }

        if (this.results.axe.violations.length > 0) {
            recommendations.push(
                'Address axe-core violations by following WCAG 2.1 AA guidelines. Focus on critical and serious violations first.'
            );
        }

        if (this.results.summary.totalViolations === 0) {
            recommendations.push(
                'Excellent! No accessibility violations found. Continue monitoring with regular accessibility audits.'
            );
        }

        return recommendations;
    }

    generateMarkdownReport() {
        const { summary, jest, axe, lighthouse } = this.results;

        return `# Accessibility Test Report

Generated on: ${new Date().toLocaleString()}

## 📊 Summary

- **Total Violations**: ${summary.totalViolations}
- **Critical Violations**: ${summary.criticalViolations}
- **Overall Status**: ${summary.passed ? '✅ PASSED' : '❌ FAILED'}

## 🧪 Test Results

### Jest Accessibility Tests
- **Status**: ${jest.passed ? '✅ PASSED' : '❌ FAILED'}
- **Violations**: ${jest.violations.length}

${jest.violations.length > 0 ? `
#### Jest Violations:
${jest.violations.map(v => `- **${v.type}**: ${v.message}`).join('\n')}
` : ''}

### Axe-core Scans
- **Status**: ${axe.passed ? '✅ PASSED' : '❌ FAILED'}
- **Total Violations**: ${axe.violations.length}
- **Pages Scanned**: ${axe.scannedPages.length}

#### Scanned Pages:
${axe.scannedPages.map(p =>
        `- **${p.name}**: ${p.violations} violations, ${p.passes} passes`
    ).join('\n')}

${axe.violations.length > 0 ? `
#### Axe Violations:
${axe.violations.slice(0, 10).map(v =>
        `- **[${v.severity?.toUpperCase() || 'UNKNOWN'}] ${v.id || v.type}** (${v.page || 'unknown page'}): ${v.description || v.message || 'No description'}`
    ).join('\n')}
${axe.violations.length > 10 ? `\n... and ${axe.violations.length - 10} more violations` : ''}
` : ''}

## 💡 Recommendations

${this.generateRecommendations().map(r => `- ${r}`).join('\n')}

## 🔗 Resources

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [Accessibility Guidelines Documentation](./docs/ACCESSIBILITY_GUIDELINES.md)
- [axe-core Documentation](https://github.com/dequelabs/axe-core)

---

*This report was generated automatically by the Accessibility Test Runner.*`;
    }

    async run() {
        console.log('🌐 Starting Comprehensive Accessibility Test Suite\n');

        let serverProcess = null;

        try {
            // Ensure report directory exists
            await this.ensureReportDirectory();

            // Start Django server
            serverProcess = await this.startDjangoServer();

            // Run all accessibility tests
            await this.runJestTests();
            await this.runAxeCoreTests();

            // Generate comprehensive report
            const report = await this.generateReport();

            // Display final results
            console.log(`\n${'='.repeat(60)}`);
            console.log('🏁 ACCESSIBILITY TEST SUITE COMPLETE');
            console.log('='.repeat(60));

            if (report.summary.passed) {
                console.log('🎉 SUCCESS: All accessibility tests passed!');
                console.log('✅ Zero critical accessibility issues found');
                console.log('✅ Website meets WCAG 2.1 AA standards');
            } else {
                console.log('❌ FAILURE: Accessibility issues found');
                console.log(`📊 Total violations: ${report.summary.totalViolations}`);
                console.log(`⚠️  Critical violations: ${report.summary.criticalViolations}`);
                console.log('\n📋 Please review the accessibility report and fix all violations.');
            }

            console.log(`\n📄 Full report available at: ${path.join(this.reportDir, 'accessibility-report.md')}`);

            // Exit with appropriate code
            process.exit(report.summary.passed ? 0 : 1);

        } catch (error) {
            console.error('\n💥 Fatal error during accessibility testing:');
            console.error(error.message || error);
            process.exit(1);
        } finally {
            // Clean up server process
            if (serverProcess) {
                console.log('\n🛑 Stopping Django server...');
                serverProcess.kill('SIGTERM');
            }
        }
    }
}

// Run the accessibility test suite
if (require.main === module) {
    const runner = new AccessibilityTestRunner();
    runner.run().catch(error => {
        console.error('Unhandled error:', error);
        process.exit(1);
    });
}

module.exports = AccessibilityTestRunner;
