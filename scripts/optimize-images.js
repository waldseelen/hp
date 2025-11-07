#!/usr/bin/env node

const fs = require('fs').promises;
const path = require('path');
const sharp = require('sharp');

async function optimizeImage(inputPath, outputDir) {
    try {
        const fileName = path.basename(inputPath, path.extname(inputPath));
        const ext = path.extname(inputPath).toLowerCase();

        if (!['.jpg', '.jpeg', '.png', '.webp', '.tiff', '.bmp'].includes(ext)) {
            return null;
        }

        await fs.mkdir(outputDir, { recursive: true });

        const originalStats = await fs.stat(inputPath);
        const originalSize = originalStats.size;

        let totalSaved = 0;
        const results = [];

        // Optimize original format
        const optimizedPath = path.join(outputDir, `${fileName}.optimized${ext}`);
        let sharpInstance = sharp(inputPath);

        if (ext === '.jpg' || ext === '.jpeg') {
            sharpInstance = sharpInstance.jpeg({ quality: 85, progressive: true });
        } else if (ext === '.png') {
            sharpInstance = sharpInstance.png({ quality: 85, progressive: true });
        }

        await sharpInstance.toFile(optimizedPath);
        const optimizedStats = await fs.stat(optimizedPath);
        const savedBytes = originalSize - optimizedStats.size;
        totalSaved += savedBytes;

        results.push({
            format: ext.replace('.', '').toUpperCase(),
            path: optimizedPath,
            size: optimizedStats.size,
            saved: savedBytes
        });

        // Generate WebP version
        const webpPath = path.join(outputDir, `${fileName}.webp`);
        await sharp(inputPath)
            .webp({ quality: 85, effort: 6 })
            .toFile(webpPath);

        const webpStats = await fs.stat(webpPath);
        const webpSaved = originalSize - webpStats.size;
        totalSaved += webpSaved;

        results.push({
            format: 'WEBP',
            path: webpPath,
            size: webpStats.size,
            saved: webpSaved
        });

        // Generate AVIF version
        const avifPath = path.join(outputDir, `${fileName}.avif`);
        await sharp(inputPath)
            .avif({ quality: 75, effort: 9 })
            .toFile(avifPath);

        const avifStats = await fs.stat(avifPath);
        const avifSaved = originalSize - avifStats.size;
        totalSaved += avifSaved;

        results.push({
            format: 'AVIF',
            path: avifPath,
            size: avifStats.size,
            saved: avifSaved
        });

        const totalCompression = ((totalSaved / (originalSize * 3)) * 100).toFixed(1);

        console.log(`Optimized: ${inputPath}`);
        console.log(`  Original: ${formatBytes(originalSize)}`);
        results.forEach(result => {
            const compression = ((result.saved / originalSize) * 100).toFixed(1);
            console.log(`  ${result.format}: ${formatBytes(result.size)} (${compression}% saved)`);
        });

        return {
            originalSize,
            totalSaved,
            totalCompression,
            formats: results.length
        };

    } catch (error) {
        console.error(`Error optimizing ${inputPath}:`, error.message);
        return null;
    }
}

function formatBytes(bytes) {
    if (bytes === 0) { return '0 B'; }
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
}

async function processDirectory(dir, outputDir) {
    const items = await fs.readdir(dir, { withFileTypes: true });
    const stats = {
        totalOriginal: 0,
        totalSaved: 0,
        files: 0,
        formats: 0
    };

    for (const item of items) {
        const fullPath = path.join(dir, item.name);
        const outputPath = path.join(outputDir, path.relative(dir, fullPath));

        if (item.isDirectory() && !item.name.includes('node_modules') && !item.name.includes('.git')) {
            const subStats = await processDirectory(fullPath, outputPath);
            stats.totalOriginal += subStats.totalOriginal;
            stats.totalSaved += subStats.totalSaved;
            stats.files += subStats.files;
            stats.formats += subStats.formats;
        } else if (item.isFile()) {
            const result = await optimizeImage(fullPath, path.dirname(outputPath));

            if (result) {
                stats.totalOriginal += result.originalSize;
                stats.totalSaved += result.totalSaved;
                stats.files++;
                stats.formats += result.formats;
            }
        }
    }

    return stats;
}

async function main() {
    const staticDir = path.join(__dirname, '..', 'static');
    const outputDir = path.join(staticDir, 'optimized');

    try {
        console.log('Starting image optimization...');

        // Process static/images directory if it exists
        const imagesDir = path.join(staticDir, 'images');
        let stats;

        try {
            await fs.access(imagesDir);
            stats = await processDirectory(imagesDir, path.join(outputDir, 'images'));
        } catch {
            // If images directory doesn't exist, process entire static directory
            stats = await processDirectory(staticDir, outputDir);
        }

        const totalCompression = stats.totalOriginal > 0
            ? ((stats.totalSaved / stats.totalOriginal) * 100).toFixed(1)
            : 0;

        console.log(`\n=== Image Optimization Complete ===`);
        console.log(`Files processed: ${stats.files}`);
        console.log(`Formats generated: ${stats.formats}`);
        console.log(`Original size: ${formatBytes(stats.totalOriginal)}`);
        console.log(`Total saved: ${formatBytes(stats.totalSaved)}`);
        console.log(`Average compression: ${totalCompression}%`);
        console.log(`Output directory: ${outputDir}`);

    } catch (error) {
        console.error('Error during image optimization:', error);
        process.exit(1);
    }
}

if (require.main === module) {
    main();
}
