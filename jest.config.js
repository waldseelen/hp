module.exports = {
    testEnvironment: 'node',
    testMatch: ['**/tests/accessibility/**/*.test.js'],
    setupFilesAfterEnv: ['<rootDir>/tests/accessibility/setup.js'],
    collectCoverageFrom: [
        'static/js/**/*.js',
        '!static/js/**/*.min.js',
        '!**/node_modules/**'
    ],
    coverageDirectory: 'coverage/accessibility',
    coverageReporters: ['text', 'lcov', 'html'],
    testTimeout: 30000,
    verbose: true,
    reporters: [
        'default',
        ['jest-html-reporters', {
            publicPath: './coverage/accessibility/html-report',
            filename: 'accessibility-report.html',
            expand: true
        }]
    ]
};
