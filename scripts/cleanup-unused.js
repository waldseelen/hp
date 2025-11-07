#!/usr/bin/env node

const fs = require('fs').promises;
const path = require('path');

async function findReferencedFiles() {
    const referencedFiles = new Set();

    // Search in templates
    const templatesDir = path.join(__dirname, '..', 'templates');
    await searchInDirectory(templatesDir, referencedFiles, ['.html']);

    // Search in Python files
    const appsDir = path.join(__dirname, '..', 'apps');
    await searchInDirectory(appsDir, referencedFiles, ['.py']);

    // Search in settings
    const settingsDir = path.join(__dirname, '..', 'portfolio_site');
    await searchInDirectory(settingsDir, referencedFiles, ['.py']);

    return referencedFiles;
}

async function searchInDirectory(dir, referencedFiles, extensions) {
    try {
        const items = await fs.readdir(dir, { withFileTypes: true });

        for (const item of items) {
            const fullPath = path.join(dir, item.name);

            if (item.isDirectory() && !item.name.includes('node_modules') && !item.name.includes('.git')) {
                await searchInDirectory(fullPath, referencedFiles, extensions);
            } else if (item.isFile() && extensions.some(ext => item.name.endsWith(ext))) {
                await searchFileForReferences(fullPath, referencedFiles);
            }
        }
    } catch (error) {
        console.log(`Skipping directory ${dir}: ${error.message}`);
    }
}

async function searchFileForReferences(filePath, referencedFiles) {
    try {
        const content = await fs.readFile(filePath, 'utf8');

        // Look for static file references
        const staticPatterns = [
            /static\/[^'"\s]+/g,
            /'static\/[^']+'/g,
            /"static\/[^"]+"/g,
            /{% load static %}/g,
            /{% static ['"][^'"]+['"] %}/g,
        ];

        for (const pattern of staticPatterns) {
            const matches = content.match(pattern);
            if (matches) {
                matches.forEach(match => {
                    // Extract the file path
                    const staticPath = match.replace(/['"`]/g, '').replace('{% static ', '').replace(' %}', '');
                    if (staticPath.startsWith('static/')) {
                        referencedFiles.add(staticPath);
                    }
                });
            }
        }
    } catch (error) {
        console.log(`Error reading ${filePath}: ${error.message}`);
    }
}

async function getAllStaticFiles() {
    const staticDir = path.join(__dirname, '..', 'static');
    const allFiles = new Set();

    await findAllFiles(staticDir, allFiles);

    return allFiles;
}

async function findAllFiles(dir, allFiles) {
    try {
        const items = await fs.readdir(dir, { withFileTypes: true });

        for (const item of items) {
            const fullPath = path.join(dir, item.name);
            const relativePath = path.relative(path.join(__dirname, '..'), fullPath);

            if (item.isDirectory()) {
                await findAllFiles(fullPath, allFiles);
            } else if (item.isFile()) {
                allFiles.add(relativePath.replace(/\\/g, '/'));
            }
        }
    } catch (error) {
        console.log(`Error reading directory ${dir}: ${error.message}`);
    }
}

function formatBytes(bytes) {
    if (bytes === 0) { return '0 B'; }
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
}

async function main() {
    try {
        console.log('🧹 Starting unused file cleanup...');

        // Find all referenced files
        console.log('📖 Scanning for file references...');
        const referencedFiles = await findReferencedFiles();
        console.log(`Found ${referencedFiles.size} referenced files`);

        // Find all static files
        console.log('📁 Scanning static files...');
        const allFiles = await getAllStaticFiles();
        console.log(`Found ${allFiles.size} total static files`);

        // Find unused files
        const unusedFiles = [];
        const backupExclusions = [
            'unused-backup/',
            'optimized/',
            '.min.js',
            '.min.css',
            '.map',
            'node_modules/',
            '.git/',
        ];

        for (const file of allFiles) {
            // Skip backup directories and generated files
            if (backupExclusions.some(exclusion => file.includes(exclusion))) {
                continue;
            }

            // Check if file is referenced
            let isReferenced = false;
            const baseFile = file.replace('static/', '');

            // Check exact match
            if (referencedFiles.has(file) || referencedFiles.has(baseFile)) {
                isReferenced = true;
            }

            // Check without extension for images (might be referenced as .webp, .avif, etc.)
            if (!isReferenced && /\.(jpg|jpeg|png|gif|webp|avif)$/i.test(file)) {
                const withoutExt = file.replace(/\.[^.]+$/, '');
                for (const ref of referencedFiles) {
                    if (ref.startsWith(withoutExt)) {
                        isReferenced = true;
                        break;
                    }
                }
            }

            if (!isReferenced) {
                unusedFiles.push(file);
            }
        }

        console.log(`\n📊 Found ${unusedFiles.length} unused files`);

        if (unusedFiles.length === 0) {
            console.log('✅ No unused files found!');
            return;
        }

        // Create backup directory
        const backupDir = path.join(__dirname, '..', 'static', 'unused-backup', new Date().toISOString().split('T')[0]);
        await fs.mkdir(backupDir, { recursive: true });

        let totalSaved = 0;
        const movedFiles = [];

        // Move unused files to backup
        for (const file of unusedFiles) {
            try {
                const fullPath = path.join(__dirname, '..', file);
                const stats = await fs.stat(fullPath);
                totalSaved += stats.size;

                // Create directory structure in backup
                const relativePath = path.relative(path.join(__dirname, '..', 'static'), fullPath);
                const backupPath = path.join(backupDir, relativePath);
                const backupDirPath = path.dirname(backupPath);

                await fs.mkdir(backupDirPath, { recursive: true });

                // Move file to backup
                await fs.rename(fullPath, backupPath);
                movedFiles.push({
                    original: file,
                    backup: path.relative(path.join(__dirname, '..'), backupPath),
                    size: stats.size
                });

                console.log(`📦 Moved: ${file} -> backup`);
            } catch (error) {
                console.log(`❌ Error moving ${file}: ${error.message}`);
            }
        }

        // Create cleanup report
        const reportPath = path.join(backupDir, 'cleanup-report.json');
        const report = {
            timestamp: new Date().toISOString(),
            total_files_scanned: allFiles.size,
            referenced_files: referencedFiles.size,
            unused_files_found: unusedFiles.length,
            files_moved: movedFiles.length,
            total_space_saved: totalSaved,
            backup_directory: path.relative(path.join(__dirname, '..'), backupDir),
            moved_files: movedFiles
        };

        await fs.writeFile(reportPath, JSON.stringify(report, null, 2));

        console.log(`\n=== Cleanup Complete ===`);
        console.log(`Files moved to backup: ${movedFiles.length}`);
        console.log(`Space saved: ${formatBytes(totalSaved)}`);
        console.log(`Backup location: ${path.relative(path.join(__dirname, '..'), backupDir)}`);
        console.log(`Report: ${path.relative(path.join(__dirname, '..'), reportPath)}`);

    } catch (error) {
        console.error('Error during cleanup:', error);
        process.exit(1);
    }
}

if (require.main === module) {
    main();
}
