#!/usr/bin/env node

/**
 * Static Assets Size Reporter
 * Reports file sizes and compression ratios for collectstatic output
 * Used in CI/CD pipeline to track asset size changes
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const zlib = require('zlib');

const CONFIG = {
    staticDir: path.join(process.cwd(), 'static'),
    staticFilesDir: path.join(process.cwd(), 'staticfiles'),
    reportPath: path.join(process.cwd(), 'docs/STATIC_ASSETS_REPORT.md'),
    jsonReportPath: path.join(process.cwd(), '.artifacts/static-sizes.json'),
};

// File extensions to analyze
const EXTENSIONS_TO_TRACK = {
    css: ['.css'],
    js: ['.js'],
    images: ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.ico'],
    fonts: ['.woff', '.woff2', '.ttf', '.eot'],
    other: []
};

function getFileSize(filePath) {
    try {
        const stats = fs.statSync(filePath);
        return stats.size;
    } catch (error) {
        return 0;
    }
}

function getCompressedSize(filePath) {
    try {
        const content = fs.readFileSync(filePath);
        return zlib.gzipSync(content).length;
    } catch (error) {
        return 0;
    }
}

function formatBytes(bytes) {
    if (bytes === 0) { return '0 B'; }
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${Math.round((bytes / Math.pow(k, i)) * 100) / 100} ${sizes[i]}`;
}

function getCategoryForFile(filename) {
    const ext = path.extname(filename).toLowerCase();
    for (const [category, extensions] of Object.entries(EXTENSIONS_TO_TRACK)) {
        if (extensions.includes(ext)) {
            return category;
        }
    }
    return 'other';
}

function walkDir(dir) {
    const files = [];
    try {
        const entries = fs.readdirSync(dir, { withFileTypes: true });
        for (const entry of entries) {
            const fullPath = path.join(dir, entry.name);
            if (entry.isDirectory()) {
                files.push(...walkDir(fullPath));
            } else {
                files.push(fullPath);
            }
        }
    } catch (error) {
        console.warn(`Warning: Could not read directory ${dir}: ${error.message}`);
    }
    return files;
}

function analyzeAssets() {
    const stats = {
        timestamp: new Date().toISOString(),
        byCategory: {},
        total: {
            raw: 0,
            compressed: 0,
            compressionRatio: 0,
            fileCount: 0,
        },
        files: []
    };

    // Initialize categories
    Object.keys(EXTENSIONS_TO_TRACK).forEach(cat => {
        stats.byCategory[cat] = {
            raw: 0,
            compressed: 0,
            fileCount: 0,
            files: []
        };
    });

    // Find all directories to analyze
    const directories = [];
    if (fs.existsSync(CONFIG.staticDir)) {
        directories.push(CONFIG.staticDir);
    }
    if (fs.existsSync(CONFIG.staticFilesDir)) {
        directories.push(CONFIG.staticFilesDir);
    }

    // Analyze files
    for (const dir of directories) {
        const files = walkDir(dir);
        for (const file of files) {
            const rawSize = getFileSize(file);
            const compressedSize = getCompressedSize(file);
            const category = getCategoryForFile(file);
            const relativePath = path.relative(process.cwd(), file);

            const fileStats = {
                path: relativePath,
                raw: rawSize,
                compressed: compressedSize,
                ratio: rawSize > 0 ? Math.round(((rawSize - compressedSize) / rawSize) * 100) : 0,
            };

            stats.files.push(fileStats);
            stats.byCategory[category].raw += rawSize;
            stats.byCategory[category].compressed += compressedSize;
            stats.byCategory[category].fileCount += 1;
            stats.byCategory[category].files.push(fileStats);

            stats.total.raw += rawSize;
            stats.total.compressed += compressedSize;
            stats.total.fileCount += 1;
        }
    }

    // Calculate compression ratios
    if (stats.total.raw > 0) {
        stats.total.compressionRatio = Math.round(
            ((stats.total.raw - stats.total.compressed) / stats.total.raw) * 100
        );
    }

    for (const category of Object.keys(stats.byCategory)) {
        const cat = stats.byCategory[category];
        if (cat.raw > 0) {
            cat.compressionRatio = Math.round(((cat.raw - cat.compressed) / cat.raw) * 100);
        }
    }

    return stats;
}

function generateMarkdownReport(stats) {
    const { byCategory, total, timestamp } = stats;

    let report = `# Static Assets Size Report

**Generated:** ${timestamp}

## Summary

| Metric | Size | Compressed | Savings |
|--------|------|-----------|---------|
| **Total** | ${formatBytes(total.raw)} | ${formatBytes(total.compressed)} | ${total.compressionRatio}% |
| **Files** | ${total.fileCount} | - | - |

## Assets by Category

| Category | Count | Raw Size | Compressed | Savings |
|----------|-------|----------|-----------|---------|`;

    for (const [category, stats] of Object.entries(byCategory)) {
        if (stats.fileCount > 0) {
            report += `
| **${category}** | ${stats.fileCount} | ${formatBytes(stats.raw)} | ${formatBytes(stats.compressed)} | ${stats.compressionRatio}% |`;
        }
    }

    report += `

## Largest Files

| File | Raw Size | Compressed | Savings |
|------|----------|-----------|---------|`;

    // Sort files by size and show top 10
    const sortedFiles = stats.files
        .sort((a, b) => b.raw - a.raw)
        .slice(0, 10);

    for (const file of sortedFiles) {
        report += `
| ${file.path} | ${formatBytes(file.raw)} | ${formatBytes(file.compressed)} | ${file.ratio}% |`;
    }

    report += `

## Compression Analysis

- **Average Compression Ratio:** ${total.compressionRatio}%
- **Total Size Reduction:** ${formatBytes(total.raw - total.compressed)}
- **Average File Size:** ${formatBytes(Math.round(total.raw / total.fileCount))}

## Gzip Compression Details

| Category | Gzip Efficiency |
|----------|-----------------|
`;

    for (const [category, catStats] of Object.entries(byCategory)) {
        if (catStats.fileCount > 0) {
            const avgFileSize = Math.round(catStats.raw / catStats.fileCount);
            report += `| ${category} | ${catStats.compressionRatio}% (avg: ${formatBytes(avgFileSize)}) |\n`;
        }
    }

    report += `

## CI/CD Integration

This report is generated as part of the static asset optimization pipeline.
Track these metrics to ensure:
- CSS bundle size stays under control
- JavaScript bundles remain optimized
- Image compression is working properly
- Gzip compression ratios are maintained

### Targets

- CSS Size: < 200KB (raw), < 50KB (gzip)
- JavaScript Size: < 500KB (raw), < 100KB (gzip)
- Images: < 2MB total
- Compression Ratio: > 70%

---

**Report generated by:** Static Assets Size Reporter
`;

    return report;
}

function saveReport(stats) {
    // Ensure artifacts directory exists
    const artifactDir = path.dirname(CONFIG.jsonReportPath);
    if (!fs.existsSync(artifactDir)) {
        fs.mkdirSync(artifactDir, { recursive: true });
    }

    // Save JSON report
    fs.writeFileSync(CONFIG.jsonReportPath, JSON.stringify(stats, null, 2));
    console.log(`✓ JSON report saved: ${CONFIG.jsonReportPath}`);

    // Save markdown report
    const markdown = generateMarkdownReport(stats);
    fs.writeFileSync(CONFIG.reportPath, markdown);
    console.log(`✓ Markdown report saved: ${CONFIG.reportPath}`);
}

function printSummary(stats) {
    console.log('\n📊 Static Assets Summary:');
    console.log(`   Total Raw Size: ${formatBytes(stats.total.raw)}`);
    console.log(`   Total Compressed: ${formatBytes(stats.total.compressed)}`);
    console.log(`   Compression Ratio: ${stats.total.compressionRatio}%`);
    console.log(`   Total Files: ${stats.total.fileCount}`);
    console.log('');
    console.log('📁 By Category:');
    for (const [category, catStats] of Object.entries(stats.byCategory)) {
        if (catStats.fileCount > 0) {
            console.log(`   ${category}: ${formatBytes(catStats.raw)} → ${formatBytes(catStats.compressed)} (${catStats.fileCount} files, ${catStats.compressionRatio}%)`);
        }
    }
}

function runReport() {
    try {
        console.log('🚀 Analyzing static assets...');

        // Run collectstatic if needed
        console.log('📦 Running collectstatic...');
        try {
            execSync('python manage.py collectstatic --noinput --clear', { stdio: 'inherit' });
        } catch (error) {
            console.warn('⚠️  collectstatic had issues, but continuing...');
        }

        // Analyze assets
        console.log('📈 Analyzing asset sizes...');
        const stats = analyzeAssets();

        // Save reports
        saveReport(stats);

        // Print summary
        printSummary(stats);

        console.log('\n✅ Report generation complete!');
        return stats;
    } catch (error) {
        console.error('❌ Report generation failed:', error);
        process.exit(1);
    }
}

// Run if called directly
if (require.main === module) {
    runReport();
}

module.exports = { analyzeAssets, generateMarkdownReport };
