#!/usr/bin/env node
/**
 * BUNDLE ANALYZER SCRIPT
 * ======================
 *
 * Analyzes static file bundles and provides optimization recommendations.
 * Generates detailed reports about file sizes, dependencies, and performance.
 *
 * FEATURES:
 * - Bundle size analysis
 * - File dependency mapping
 * - Performance recommendations
 * - Detailed reporting (JSON, HTML)
 * - Optimization suggestions
 *
 * USAGE:
 *   node scripts/analyze-bundle.js
 *   npm run analyze:bundle
 */

const fs = require('fs');
const path = require('path');
const { glob } = require('glob');

class BundleAnalyzer {
    constructor() {
        this.config = {
            staticDir: 'static',
            outputDir: 'reports',
            thresholds: {
                large_file: 100 * 1024, // 100KB
                huge_file: 500 * 1024, // 500KB
                total_bundle: 2 * 1024 * 1024 // 2MB
            }
        };

        this.analysis = {
            files: [],
            dependencies: new Map(),
            duplicates: [],
            recommendations: [],
            stats: {
                totalFiles: 0,
                totalSize: 0,
                largestFile: null,
                largestSize: 0,
                avgFileSize: 0
            }
        };
    }

    async initialize() {
        console.log('📊 Bundle Analysis Started');
        console.log('===========================');

        // Create reports directory
        if (!fs.existsSync(this.config.outputDir)) {
            fs.mkdirSync(this.config.outputDir, { recursive: true });
            console.log(`📁 Created reports directory: ${this.config.outputDir}`);
        }
    }

    async analyzeFiles() {
        console.log('🔍 Analyzing static files...');

        const fileTypes = ['css', 'js', 'png', 'jpg', 'jpeg', 'gif', 'webp', 'avif', 'svg', 'woff', 'woff2', 'ttf'];
        const patterns = fileTypes.map(ext => `${this.config.staticDir}/**/*.${ext}`);

        let allFiles = [];
        for (const pattern of patterns) {
            const matches = glob.sync(pattern, {
                ignore: [
                    '**/node_modules/**',
                    '**/.git/**',
                    '**/unused-backup/**'
                ]
            });
            allFiles = allFiles.concat(matches);
        }

        // Analyze each file
        for (const filePath of allFiles) {
            const fileInfo = await this.analyzeFile(filePath);
            if (fileInfo) {
                this.analysis.files.push(fileInfo);
            }
        }

        // Calculate statistics
        this.calculateStats();

        console.log(`📊 Analyzed ${this.analysis.files.length} files`);
    }

    async analyzeFile(filePath) {
        try {
            const stats = fs.statSync(filePath);
            const ext = path.extname(filePath).toLowerCase();
            const relativePath = path.relative(this.config.staticDir, filePath);

            const fileInfo = {
                path: filePath,
                relativePath: relativePath,
                name: path.basename(filePath),
                extension: ext,
                size: stats.size,
                type: this.getFileType(ext),
                isLarge: stats.size > this.config.thresholds.large_file,
                isHuge: stats.size > this.config.thresholds.huge_file,
                dependencies: [],
                isDuplicate: false,
                compressionRatio: null
            };

            // Analyze file content for dependencies (CSS/JS only)
            if (ext === '.css' || ext === '.js') {
                fileInfo.dependencies = await this.findDependencies(filePath);
            }

            // Estimate compression potential
            if (ext === '.css' || ext === '.js') {
                fileInfo.compressionRatio = await this.estimateCompression(filePath);
            }

            return fileInfo;

        } catch (error) {
            console.warn(`⚠️  Could not analyze ${filePath}: ${error.message}`);
            return null;
        }
    }

    getFileType(extension) {
        const typeMap = {
            '.css': 'stylesheet',
            '.js': 'script',
            '.png': 'image',
            '.jpg': 'image',
            '.jpeg': 'image',
            '.gif': 'image',
            '.webp': 'image',
            '.avif': 'image',
            '.svg': 'image',
            '.woff': 'font',
            '.woff2': 'font',
            '.ttf': 'font',
            '.eot': 'font'
        };

        return typeMap[extension] || 'other';
    }

    async findDependencies(filePath) {
        try {
            const content = fs.readFileSync(filePath, 'utf8');
            const dependencies = [];
            const ext = path.extname(filePath);

            if (ext === '.css') {
                // Find @import statements
                const importRegex = /@import\s+['"]([^'"]+)['"]/g;
                let match;
                while ((match = importRegex.exec(content)) !== null) {
                    dependencies.push(match[1]);
                }

                // Find url() references
                const urlRegex = /url\(['"]?([^'")]+)['"]?\)/g;
                while ((match = urlRegex.exec(content)) !== null) {
                    dependencies.push(match[1]);
                }
            } else if (ext === '.js') {
                // Find import/require statements
                const importRegex = /(?:import.*from\s+['"]([^'"]+)['"]|require\(['"]([^'"]+)['"]\))/g;
                let match;
                while ((match = importRegex.exec(content)) !== null) {
                    dependencies.push(match[1] || match[2]);
                }
            }

            return dependencies;

        } catch (error) {
            return [];
        }
    }

    async estimateCompression(filePath) {
        try {
            const content = fs.readFileSync(filePath, 'utf8');
            const originalSize = Buffer.byteLength(content, 'utf8');

            // Simple estimation based on repetitive patterns
            const uniqueChars = new Set(content).size;
            const totalChars = content.length;

            // Rough estimate: more unique characters = less compressible
            const compressionRatio = Math.max(0.3, Math.min(0.9, uniqueChars / totalChars));
            return compressionRatio;

        } catch (error) {
            return null;
        }
    }

    calculateStats() {
        const stats = this.analysis.stats;

        stats.totalFiles = this.analysis.files.length;
        stats.totalSize = this.analysis.files.reduce((sum, file) => sum + file.size, 0);

        if (stats.totalFiles > 0) {
            stats.avgFileSize = stats.totalSize / stats.totalFiles;

            // Find largest file
            const largestFile = this.analysis.files.reduce((largest, current) =>
                current.size > largest.size ? current : largest
            );

            stats.largestFile = largestFile.relativePath;
            stats.largestSize = largestFile.size;
        }
    }

    async findDuplicates() {
        console.log('🔍 Finding duplicate files...');

        const hashMap = new Map();

        for (const file of this.analysis.files) {
            try {
                const content = fs.readFileSync(file.path);
                const hash = require('crypto').createHash('md5').update(content).digest('hex');

                if (hashMap.has(hash)) {
                    const existing = hashMap.get(hash);
                    file.isDuplicate = true;
                    existing.isDuplicate = true;

                    // Add to duplicates array if not already present
                    const duplicateGroup = this.analysis.duplicates.find(group =>
                        group.some(f => f.path === existing.path)
                    );

                    if (duplicateGroup) {
                        duplicateGroup.push(file);
                    } else {
                        this.analysis.duplicates.push([existing, file]);
                    }
                } else {
                    hashMap.set(hash, file);
                }
            } catch (error) {
                // Skip files that can't be read
            }
        }

        console.log(`📊 Found ${this.analysis.duplicates.length} duplicate groups`);
    }

    generateRecommendations() {
        console.log('💡 Generating recommendations...');

        const recommendations = [];
        const stats = this.analysis.stats;

        // Bundle size recommendations
        if (stats.totalSize > this.config.thresholds.total_bundle) {
            recommendations.push({
                type: 'bundle_size',
                severity: 'high',
                title: 'Bundle size exceeds recommended limit',
                description: `Total bundle size is ${this.formatBytes(stats.totalSize)}, which exceeds the recommended ${this.formatBytes(this.config.thresholds.total_bundle)} limit.`,
                suggestions: [
                    'Consider code splitting for JavaScript files',
                    'Implement lazy loading for non-critical assets',
                    'Remove unused CSS and JavaScript',
                    'Optimize images with modern formats (WebP, AVIF)'
                ]
            });
        }

        // Large files recommendations
        const largeFiles = this.analysis.files.filter(f => f.isHuge);
        if (largeFiles.length > 0) {
            recommendations.push({
                type: 'large_files',
                severity: 'medium',
                title: `${largeFiles.length} files are very large`,
                description: `Files larger than ${this.formatBytes(this.config.thresholds.huge_file)} can impact loading performance.`,
                files: largeFiles.map(f => ({ path: f.relativePath, size: f.size })),
                suggestions: [
                    'Minify CSS and JavaScript files',
                    'Compress images with appropriate quality settings',
                    'Consider splitting large files into smaller chunks',
                    'Use modern image formats for better compression'
                ]
            });
        }

        // Duplicate files recommendations
        if (this.analysis.duplicates.length > 0) {
            const totalDuplicateSize = this.analysis.duplicates.reduce((sum, group) => sum + (group.length - 1) * group[0].size, 0);

            recommendations.push({
                type: 'duplicates',
                severity: 'medium',
                title: `${this.analysis.duplicates.length} duplicate file groups found`,
                description: `Duplicate files waste ${this.formatBytes(totalDuplicateSize)} of space.`,
                duplicates: this.analysis.duplicates,
                suggestions: [
                    'Remove or deduplicate identical files',
                    'Use build tools to prevent duplicate file generation',
                    'Implement proper asset management'
                ]
            });
        }

        // Compression recommendations
        const uncompressedFiles = this.analysis.files.filter(f =>
            (f.type === 'stylesheet' || f.type === 'script') &&
            !f.name.includes('.min.') &&
            f.compressionRatio && f.compressionRatio < 0.7
        );

        if (uncompressedFiles.length > 0) {
            recommendations.push({
                type: 'compression',
                severity: 'low',
                title: `${uncompressedFiles.length} files could benefit from minification`,
                description: 'Minification can significantly reduce file sizes for CSS and JavaScript.',
                files: uncompressedFiles.map(f => ({
                    path: f.relativePath,
                    size: f.size,
                    estimatedSaving: Math.round(f.size * (1 - f.compressionRatio))
                })),
                suggestions: [
                    'Run npm run minify:css to minify CSS files',
                    'Run npm run minify:js to minify JavaScript files',
                    'Set up automated minification in build process'
                ]
            });
        }

        this.analysis.recommendations = recommendations;
        console.log(`📊 Generated ${recommendations.length} recommendations`);
    }

    async generateReports() {
        console.log('📄 Generating reports...');

        // Generate JSON report
        const jsonReport = {
            timestamp: new Date().toISOString(),
            stats: this.analysis.stats,
            files: this.analysis.files,
            duplicates: this.analysis.duplicates,
            recommendations: this.analysis.recommendations
        };

        const jsonPath = path.join(this.config.outputDir, 'bundle-analysis.json');
        fs.writeFileSync(jsonPath, JSON.stringify(jsonReport, null, 2));

        // Generate HTML report
        const htmlReport = this.generateHTMLReport(jsonReport);
        const htmlPath = path.join(this.config.outputDir, 'bundle-analysis.html');
        fs.writeFileSync(htmlPath, htmlReport);

        console.log(`📄 Reports generated:`);
        console.log(`   JSON: ${jsonPath}`);
        console.log(`   HTML: ${htmlPath}`);
    }

    generateHTMLReport(data) {
        return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bundle Analysis Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header { border-bottom: 2px solid #007acc; padding-bottom: 20px; margin-bottom: 30px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: #f8f9fa; padding: 20px; border-radius: 6px; border-left: 4px solid #007acc; }
        .stat-value { font-size: 2em; font-weight: bold; color: #007acc; }
        .stat-label { color: #666; margin-top: 5px; }
        .section { margin-bottom: 40px; }
        .section h2 { color: #333; border-bottom: 1px solid #eee; padding-bottom: 10px; }
        .recommendation { background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 6px; padding: 15px; margin-bottom: 15px; }
        .recommendation.high { background: #f8d7da; border-color: #f5c6cb; }
        .recommendation.medium { background: #d1ecf1; border-color: #bee5eb; }
        .file-list { max-height: 300px; overflow-y: auto; }
        .file-item { display: flex; justify-content: space-between; padding: 8px; border-bottom: 1px solid #eee; }
        .file-item:hover { background: #f8f9fa; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { text-align: left; padding: 12px; border-bottom: 1px solid #eee; }
        th { background: #f8f9fa; font-weight: bold; }
        .size { text-align: right; font-family: monospace; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Bundle Analysis Report</h1>
            <p>Generated on ${new Date(data.timestamp).toLocaleString()}</p>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">${data.stats.totalFiles}</div>
                <div class="stat-label">Total Files</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${this.formatBytes(data.stats.totalSize)}</div>
                <div class="stat-label">Total Size</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${this.formatBytes(data.stats.avgFileSize)}</div>
                <div class="stat-label">Average File Size</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${this.formatBytes(data.stats.largestSize)}</div>
                <div class="stat-label">Largest File</div>
            </div>
        </div>

        <div class="section">
            <h2>Recommendations</h2>
            ${data.recommendations.map(rec => `
                <div class="recommendation ${rec.severity}">
                    <h3>${rec.title}</h3>
                    <p>${rec.description}</p>
                    <ul>
                        ${rec.suggestions.map(s => `<li>${s}</li>`).join('')}
                    </ul>
                </div>
            `).join('')}
        </div>

        <div class="section">
            <h2>File Breakdown by Type</h2>
            <table>
                <thead>
                    <tr><th>Type</th><th>Count</th><th>Total Size</th><th>Average Size</th></tr>
                </thead>
                <tbody>
                    ${this.getFileTypeStats(data.files).map(type => `
                        <tr>
                            <td>${type.name}</td>
                            <td>${type.count}</td>
                            <td class="size">${this.formatBytes(type.totalSize)}</td>
                            <td class="size">${this.formatBytes(type.avgSize)}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>

        <div class="section">
            <h2>Largest Files</h2>
            <div class="file-list">
                ${data.files
        .sort((a, b) => b.size - a.size)
        .slice(0, 20)
        .map(file => `
                        <div class="file-item">
                            <span>${file.relativePath}</span>
                            <span class="size">${this.formatBytes(file.size)}</span>
                        </div>
                    `).join('')}
            </div>
        </div>
    </div>
</body>
</html>`;
    }

    getFileTypeStats(files) {
        const typeStats = {};

        files.forEach(file => {
            if (!typeStats[file.type]) {
                typeStats[file.type] = {
                    name: file.type,
                    count: 0,
                    totalSize: 0
                };
            }

            typeStats[file.type].count++;
            typeStats[file.type].totalSize += file.size;
        });

        return Object.values(typeStats).map(type => ({
            ...type,
            avgSize: type.totalSize / type.count
        })).sort((a, b) => b.totalSize - a.totalSize);
    }

    formatBytes(bytes) {
        if (bytes === 0) { return '0 B'; }
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
    }

    async run() {
        await this.initialize();

        // Analyze all files
        await this.analyzeFiles();

        // Find duplicates
        await this.findDuplicates();

        // Generate recommendations
        this.generateRecommendations();

        // Generate reports
        await this.generateReports();

        // Print summary
        this.printSummary();
    }

    printSummary() {
        const stats = this.analysis.stats;

        console.log('\n📊 BUNDLE ANALYSIS SUMMARY');
        console.log('===========================');
        console.log(`Total files: ${stats.totalFiles}`);
        console.log(`Total size: ${this.formatBytes(stats.totalSize)}`);
        console.log(`Largest file: ${stats.largestFile} (${this.formatBytes(stats.largestSize)})`);
        console.log(`Average file size: ${this.formatBytes(stats.avgFileSize)}`);
        console.log(`Duplicates found: ${this.analysis.duplicates.length} groups`);
        console.log(`Recommendations: ${this.analysis.recommendations.length}`);

        if (stats.totalSize > this.config.thresholds.total_bundle) {
            console.log('\n⚠️  Bundle size exceeds recommended limit!');
        }

        console.log('\n✅ Analysis completed successfully!');
        console.log(`📄 View detailed report: ${this.config.outputDir}/bundle-analysis.html`);
    }
}

// Run the analyzer if called directly
if (require.main === module) {
    const analyzer = new BundleAnalyzer();
    analyzer.run().catch(error => {
        console.error('💥 Analysis failed:', error);
        process.exit(1);
    });
}

module.exports = BundleAnalyzer;
