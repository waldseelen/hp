# Accessibility Test Report

Generated on: 24.09.2025 08:24:53

## 📊 Summary

- **Total Violations**: 5
- **Critical Violations**: 5
- **Overall Status**: ❌ FAILED

## 🧪 Test Results

### Jest Accessibility Tests
- **Status**: ❌ FAILED
- **Violations**: 1


#### Jest Violations:
- **Jest Test Failure**: Error: Could not resolve a module for a custom reporter.
  Module name: jest-html-reporters
    at D:\FILES\BEST\node_modules\jest-config\build\index.js:1551:15
    at Array.map (<anonymous>)
    at normalizeReporters (D:\FILES\BEST\node_modules\jest-config\build\index.js:1539:20)
    at D:\FILES\BEST\node_modules\jest-config\build\index.js:1760:17
    at Array.reduce (<anonymous>)
    at normalize (D:\FILES\BEST\node_modules\jest-config\build\index.js:1658:14)
    at readConfig (D:\FILES\BEST\node_modules\jest-config\build\index.js:928:36)
    at async readConfigs (D:\FILES\BEST\node_modules\jest-config\build\index.js:1168:26)
    at async runCLI (D:\FILES\BEST\node_modules\@jest\core\build\index.js:1397:7)
    at async Object.run (D:\FILES\BEST\node_modules\jest-cli\build\index.js:656:9)



### Axe-core Scans
- **Status**: ❌ FAILED
- **Total Violations**: 4
- **Pages Scanned**: 0

#### Scanned Pages:



#### Axe Violations:
- **[CRITICAL] Axe Scan Failure** (home): error: unknown option '--reporter'
(Did you mean --no-reporter?)

- **[CRITICAL] Axe Scan Failure** (contact): error: unknown option '--reporter'
(Did you mean --no-reporter?)

- **[CRITICAL] Axe Scan Failure** (blog): error: unknown option '--reporter'
(Did you mean --no-reporter?)

- **[CRITICAL] Axe Scan Failure** (tools): error: unknown option '--reporter'
(Did you mean --no-reporter?)




## 💡 Recommendations

- Fix Jest accessibility test failures by reviewing test output and addressing the underlying accessibility issues.
- Address axe-core violations by following WCAG 2.1 AA guidelines. Focus on critical and serious violations first.

## 🔗 Resources

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [Accessibility Guidelines Documentation](./docs/ACCESSIBILITY_GUIDELINES.md)
- [axe-core Documentation](https://github.com/dequelabs/axe-core)

---

*This report was generated automatically by the Accessibility Test Runner.*