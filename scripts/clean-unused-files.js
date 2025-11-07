#!/usr/bin/env node
/**
 * UNUSED FILES CLEANUP SCRIPT
 * ============================
 *
 * Identifies and removes unused static files from Django portfolio project.
 * Scans templates and source files to find referenced static assets.
 *
 * FEATURES:
 * - Scans HTML templates for static file references
 * - Checks CSS files for imported/referenced assets
 * - Identifies unused JavaScript files
 * - Safe mode with backup before deletion
 * - Detailed reporting and statistics
 * - Whitelist for important files
 *
 * USAGE:
 *   node scripts/clean-unused-files.js
 *   node scripts/clean-unused-files.js --dry-run
 *   npm run clean:unused
 */

const fs = require('fs');
const path = require('path');
const { glob } = require('glob');

class UnusedFileCleaner {
    constructor(options = {}) {
        this.config = {
            staticDir: 'static',
            templatesDir: 'templates',
            sourceFiles: ['**/*.py', '**/*.html', '**/*.css', '**/*.js'],
            backupDir: 'static/unused-backup',
            dryRun: options.dryRun || process.argv.includes('--dry-run'),
            whitelist: [
                // Admin files
                'admin/**/*',
                // Critical CSS files
                'css/critical/*',
                'css/optimized/*',
                'css/purged/*',
                // Minified files
                '**/*.min.js',
                '**/*.min.css',
                // Favicons and manifest
                'favicon.ico',
                'manifest.json',
                'robots.txt',
                // Service worker
                'sw.js',
                // Generated files that might not be directly referenced
                '**/*-[0-9]*w.*' // Responsive images
            ],
            stats: {
                scanned: 0,
                unused: 0,
                deleted: 0,
                errors: 0,
                savedBytes: 0
            }
        };

        this.referencedFiles = new Set();
        this.staticFiles = new Set();
    }

    async initialize() {
        console.log('🧹 Unused Files Cleanup Started');
        if (this.config.dryRun) {
            console.log('🔍 DRY RUN MODE - No files will be deleted');
        }
        console.log('==================================');

        if (!this.config.dryRun && !fs.existsSync(this.config.backupDir)) {
            fs.mkdirSync(this.config.backupDir, { recursive: true });
            console.log(`📁 Created backup directory: ${this.config.backupDir}`);
        }
    }

    async findStaticFiles() {
        console.log('📂 Scanning static files...');

        const patterns = [
            `${this.config.staticDir}/**/*.*`
        ];

        let files = [];
        for (const pattern of patterns) {
            const matches = glob.sync(pattern, {
                ignore: [
                    '**/node_modules/**',
                    '**/.git/**',
                    '**/unused-backup/**'
                ]
            });
            files = files.concat(matches);
        }

        // Filter out directories and add to staticFiles set
        for (const file of files) {
            const stat = fs.statSync(file);
            if (stat.isFile()) {
                this.staticFiles.add(file);
            }
        }

        console.log(`📊 Found ${this.staticFiles.size} static files`);
        return Array.from(this.staticFiles);
    }

    async scanTemplateFiles() {
        console.log('🔍 Scanning template files for references...');

        const templateFiles = glob.sync(`${this.config.templatesDir}/**/*.html`);

        for (const templateFile of templateFiles) {
            await this.scanFileForReferences(templateFile, 'template');
        }

        console.log(`📊 Scanned ${templateFiles.length} template files`);
    }

    async scanSourceFiles() {
        console.log('🔍 Scanning source files for references...');

        const patterns = [
            'apps/**/*.py',
            'portfolio_site/**/*.py',
            'static/**/*.css',
            'static/**/*.js'
        ];

        let sourceFiles = [];
        for (const pattern of patterns) {
            const matches = glob.sync(pattern, {
                ignore: [
                    '**/node_modules/**',
                    '**/.git/**',
                    '**/unused-backup/**',
                    '**/*.min.js',
                    '**/*.min.css'
                ]
            });
            sourceFiles = sourceFiles.concat(matches);
        }

        for (const sourceFile of sourceFiles) {
            await this.scanFileForReferences(sourceFile, 'source');
        }

        console.log(`📊 Scanned ${sourceFiles.length} source files`);
    }

    async scanFileForReferences(filePath, fileType) {
        try {
            const content = fs.readFileSync(filePath, 'utf8');
            const patterns = [
                // Django static template tags
                /{% *static *['"](.*?)['"] *%}/g,
                // CSS url() references
                /url\(['"]?(.*?)['"]?\)/g,
                // HTML src and href attributes
                /(?:src|href)=['"]([^'"]*static[^'"]*)['"]/g,
                // JavaScript import/require
                /(?:import|require)\(['"]([^'"]*)['"]\)/g,
                // Direct static path references
                /['"]([^'"]*\/static\/[^'"]*)['"]/g,
                // CSS @import statements
                /@import\s+['"]([^'"]*)['"]/g
            ];

            for (const pattern of patterns) {
                let match;
                while ((match = pattern.exec(content)) !== null) {
                    let referencedPath = match[1];

                    // Normalize path
                    if (referencedPath.startsWith('/static/')) {
                        referencedPath = referencedPath.substring(1); // Remove leading /
                    } else if (!referencedPath.startsWith('static/')) {
                        referencedPath = `static/${referencedPath}`;
                    }

                    // Handle query parameters and fragments
                    referencedPath = referencedPath.split('?')[0].split('#')[0];

                    this.referencedFiles.add(referencedPath);
                }
            }

            this.config.stats.scanned++;

        } catch (error) {
            console.warn(`⚠️  Could not scan ${filePath}: ${error.message}`);
        }
    }

    isWhitelisted(filePath) {
        const relativePath = path.relative('static', filePath);

        return this.config.whitelist.some(pattern => {
            // Convert glob pattern to regex
            const regex = new RegExp(`^${pattern.replace(/\*\*/g, '.*').replace(/\*/g, '[^/]*')}$`);
            return regex.test(relativePath) || regex.test(filePath);
        });
    }

    async findUnusedFiles() {
        console.log('🔍 Identifying unused files...');

        const unusedFiles = [];

        for (const staticFile of this.staticFiles) {
            // Skip if whitelisted
            if (this.isWhitelisted(staticFile)) {
                continue;
            }

            // Check if file is referenced
            const isReferenced = this.referencedFiles.has(staticFile);

            if (!isReferenced) {
                // Additional checks for special cases
                const fileName = path.basename(staticFile);
                const fileExt = path.extname(staticFile);

                // Check for files that might be referenced by name only
                const nameReferencedPatterns = [
                    fileName,
                    fileName.replace(fileExt, ''),
                    path.relative('static', staticFile)
                ];

                let foundReference = false;
                for (const referencedFile of this.referencedFiles) {
                    for (const pattern of nameReferencedPatterns) {
                        if (referencedFile.includes(pattern)) {
                            foundReference = true;
                            break;
                        }
                    }
                    if (foundReference) { break; }
                }

                if (!foundReference) {
                    const stat = fs.statSync(staticFile);
                    unusedFiles.push({
                        path: staticFile,
                        size: stat.size,
                        relativePath: path.relative('static', staticFile)
                    });
                }
            }
        }

        console.log(`📊 Found ${unusedFiles.length} unused files`);
        return unusedFiles;
    }

    async removeUnusedFiles(unusedFiles) {
        console.log(`🗑️  ${this.config.dryRun ? 'Would remove' : 'Removing'} unused files...\n`);

        for (const file of unusedFiles) {
            try {
                if (!this.config.dryRun) {
                    // Create backup
                    const backupPath = path.join(this.config.backupDir, file.relativePath);
                    const backupDir = path.dirname(backupPath);

                    if (!fs.existsSync(backupDir)) {
                        fs.mkdirSync(backupDir, { recursive: true });
                    }

                    fs.copyFileSync(file.path, backupPath);
                    fs.unlinkSync(file.path);

                    this.config.stats.deleted++;
                }

                this.config.stats.savedBytes += file.size;
                console.log(`${this.config.dryRun ? '🔍' : '🗑️'} ${file.relativePath} (${this.formatBytes(file.size)})`);

            } catch (error) {
                this.config.stats.errors++;
                console.error(`❌ Error removing ${file.path}: ${error.message}`);
            }
        }

        this.config.stats.unused = unusedFiles.length;
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

        // Step 1: Find all static files
        await this.findStaticFiles();

        // Step 2: Scan templates for references
        await this.scanTemplateFiles();

        // Step 3: Scan source files for references
        await this.scanSourceFiles();

        console.log(`\n📊 Found ${this.referencedFiles.size} referenced files`);

        // Step 4: Find unused files
        const unusedFiles = await this.findUnusedFiles();

        if (unusedFiles.length === 0) {
            console.log('\n✅ No unused files found!');
            return;
        }

        // Step 5: Remove unused files
        await this.removeUnusedFiles(unusedFiles);

        // Step 6: Print summary
        this.printSummary();
    }

    printSummary() {
        const stats = this.config.stats;

        console.log('\n📊 CLEANUP SUMMARY');
        console.log('==================');
        console.log(`Files scanned: ${stats.scanned}`);
        console.log(`Static files found: ${this.staticFiles.size}`);
        console.log(`Referenced files: ${this.referencedFiles.size}`);
        console.log(`Unused files: ${stats.unused}`);

        if (!this.config.dryRun) {
            console.log(`Files deleted: ${stats.deleted}`);
            console.log(`Backup directory: ${this.config.backupDir}`);
        }

        console.log(`Space ${this.config.dryRun ? 'that would be' : ''} saved: ${this.formatBytes(stats.savedBytes)}`);

        if (stats.errors > 0) {
            console.log(`\n⚠️  ${stats.errors} errors occurred during cleanup`);
        }

        if (stats.unused > 0) {
            console.log(`\n✅ Cleanup ${this.config.dryRun ? 'analysis' : ''} completed successfully!`);

            if (this.config.dryRun) {
                console.log('\n💡 Run without --dry-run to actually remove files');
            } else {
                console.log('\n💡 Files have been backed up before deletion');
                console.log('💡 You can restore files from the backup directory if needed');
            }
        }
    }
}

// Run the cleaner if called directly
if (require.main === module) {
    const cleaner = new UnusedFileCleaner();
    cleaner.run().catch(error => {
        console.error('💥 Cleanup failed:', error);
        process.exit(1);
    });
}

module.exports = UnusedFileCleaner;
