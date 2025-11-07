#!/usr/bin/env node
/**
 * IMAGE COMPRESSION SCRIPT
 * =========================
 *
 * Advanced image optimization tool for Django portfolio project.
 * Compresses and converts images to modern formats (WebP, AVIF).
 *
 * FEATURES:
 * - Supports JPEG, PNG, GIF, SVG
 * - Converts to WebP and AVIF formats
 * - Maintains quality while reducing size
 * - Preserves originals in backup folder
 * - Compression statistics
 * - Responsive image generation
 *
 * USAGE:
 *   node scripts/compress-images.js
 *   npm run compress:images
 */

const fs = require('fs');
const path = require('path');
const sharp = require('sharp');
const { glob } = require('glob');

class ImageCompressor {
    constructor() {
        this.config = {
            sourceDir: 'static/images',
            outputDir: 'static/images/optimized',
            backupDir: 'static/images/originals',
            formats: ['webp', 'avif'],
            quality: {
                jpeg: 85,
                png: 90,
                webp: 80,
                avif: 75
            },
            responsiveSizes: [320, 640, 768, 1024, 1280, 1920],
            stats: {
                processed: 0,
                errors: 0,
                originalSize: 0,
                compressedSize: 0,
                savedBytes: 0
            }
        };
    }

    async initialize() {
        console.log('🖼️  Image Compression Started');
        console.log('==============================');

        // Create directories
        [this.config.outputDir, this.config.backupDir].forEach(dir => {
            if (!fs.existsSync(dir)) {
                fs.mkdirSync(dir, { recursive: true });
                console.log(`📁 Created directory: ${dir}`);
            }
        });
    }

    async findImageFiles() {
        const patterns = [
            `${this.config.sourceDir}/**/*.{jpg,jpeg,png,gif,webp}`,
            `${this.config.sourceDir}/*.{jpg,jpeg,png,gif,webp}`
        ];

        let files = [];
        for (const pattern of patterns) {
            const matches = glob.sync(pattern, {
                ignore: [
                    '**/optimized/**',
                    '**/originals/**',
                    '**/node_modules/**'
                ]
            });
            files = files.concat(matches);
        }

        return [...new Set(files)];
    }

    async getImageInfo(filePath) {
        try {
            const metadata = await sharp(filePath).metadata();
            const stats = fs.statSync(filePath);

            return {
                width: metadata.width,
                height: metadata.height,
                format: metadata.format,
                size: stats.size,
                hasAlpha: metadata.hasAlpha,
                density: metadata.density
            };
        } catch (error) {
            console.error(`❌ Error reading ${filePath}: ${error.message}`);
            return null;
        }
    }

    async compressImage(filePath) {
        try {
            const imageInfo = await this.getImageInfo(filePath);
            if (!imageInfo) { return { success: false, error: 'Could not read image metadata' }; }

            const fileName = path.parse(filePath).name;
            const relativeDir = path.relative(this.config.sourceDir, path.dirname(filePath));
            const outputDir = path.join(this.config.outputDir, relativeDir);
            const backupPath = path.join(this.config.backupDir, path.relative(this.config.sourceDir, filePath));

            // Create output directory
            if (!fs.existsSync(outputDir)) {
                fs.mkdirSync(outputDir, { recursive: true });
            }

            // Backup original if not already backed up
            if (!fs.existsSync(backupPath)) {
                const backupDir = path.dirname(backupPath);
                if (!fs.existsSync(backupDir)) {
                    fs.mkdirSync(backupDir, { recursive: true });
                }
                fs.copyFileSync(filePath, backupPath);
            }

            const results = [];
            const sharp_instance = sharp(filePath);

            // Optimize original format
            const originalExt = path.extname(filePath).toLowerCase();
            const originalOutputPath = path.join(outputDir, `${fileName}${originalExt}`);

            let optimizedSharp = sharp_instance.clone();

            if (originalExt === '.jpg' || originalExt === '.jpeg') {
                optimizedSharp = optimizedSharp.jpeg({
                    quality: this.config.quality.jpeg,
                    progressive: true,
                    mozjpeg: true
                });
            } else if (originalExt === '.png') {
                optimizedSharp = optimizedSharp.png({
                    quality: this.config.quality.png,
                    compressionLevel: 9,
                    progressive: true
                });
            }

            await optimizedSharp.toFile(originalOutputPath);
            const originalCompressedSize = fs.statSync(originalOutputPath).size;
            results.push({
                format: originalExt.replace('.', ''),
                path: originalOutputPath,
                size: originalCompressedSize
            });

            // Generate modern formats
            for (const format of this.config.formats) {
                const outputPath = path.join(outputDir, `${fileName}.${format}`);

                let formatSharp = sharp_instance.clone();

                if (format === 'webp') {
                    formatSharp = formatSharp.webp({
                        quality: this.config.quality.webp,
                        effort: 6
                    });
                } else if (format === 'avif') {
                    formatSharp = formatSharp.avif({
                        quality: this.config.quality.avif,
                        effort: 9
                    });
                }

                await formatSharp.toFile(outputPath);
                const formatSize = fs.statSync(outputPath).size;
                results.push({
                    format: format,
                    path: outputPath,
                    size: formatSize
                });
            }

            // Generate responsive versions for large images
            if (imageInfo.width > 640) {
                for (const width of this.config.responsiveSizes) {
                    if (width < imageInfo.width) {
                        const responsiveOutputPath = path.join(outputDir, `${fileName}-${width}w.webp`);

                        await sharp_instance
                            .clone()
                            .resize(width, null, {
                                withoutEnlargement: true,
                                fit: 'inside'
                            })
                            .webp({
                                quality: this.config.quality.webp,
                                effort: 6
                            })
                            .toFile(responsiveOutputPath);

                        const responsiveSize = fs.statSync(responsiveOutputPath).size;
                        results.push({
                            format: `webp-${width}w`,
                            path: responsiveOutputPath,
                            size: responsiveSize
                        });
                    }
                }
            }

            // Calculate total savings
            const totalCompressedSize = results.reduce((sum, result) => sum + result.size, 0);
            const savedBytes = imageInfo.size - Math.min(...results.map(r => r.size));
            const savedPercentage = imageInfo.size > 0 ? ((savedBytes / imageInfo.size) * 100).toFixed(1) : '0.0';

            // Update statistics
            this.config.stats.processed++;
            this.config.stats.originalSize += imageInfo.size;
            this.config.stats.compressedSize += totalCompressedSize;
            this.config.stats.savedBytes += savedBytes;

            console.log(`✅ ${filePath}`);
            console.log(`   📊 ${this.formatBytes(imageInfo.size)} → ${this.formatBytes(Math.min(...results.map(r => r.size)))} (${savedPercentage}% saved)`);
            console.log(`   📐 ${imageInfo.width}×${imageInfo.height} ${imageInfo.format.toUpperCase()}`);
            console.log(`   🎯 Generated ${results.length} optimized versions:`);

            results.forEach(result => {
                const relativePath = path.relative('static', result.path);
                console.log(`      ${result.format.padEnd(8)} ${this.formatBytes(result.size).padStart(8)} → ${relativePath}`);
            });

            return {
                success: true,
                originalSize: imageInfo.size,
                results: results,
                savedBytes,
                savedPercentage
            };

        } catch (error) {
            this.config.stats.errors++;
            console.error(`❌ Error compressing ${filePath}:`);
            console.error(`   ${error.message}`);

            return {
                success: false,
                error: error.message
            };
        }
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

        const imageFiles = await this.findImageFiles();

        if (imageFiles.length === 0) {
            console.log('⚠️  No images found to compress');
            return;
        }

        console.log(`📦 Found ${imageFiles.length} images to process\n`);

        // Process each image
        for (const file of imageFiles) {
            await this.compressImage(file);
            console.log(''); // Empty line for readability
        }

        // Print summary statistics
        this.printSummary();
    }

    printSummary() {
        const stats = this.config.stats;
        const totalSavedPercentage = stats.originalSize > 0
            ? ((stats.savedBytes / stats.originalSize) * 100).toFixed(1)
            : '0.0';

        console.log('📊 IMAGE COMPRESSION SUMMARY');
        console.log('============================');
        console.log(`Images processed: ${stats.processed}`);
        console.log(`Errors: ${stats.errors}`);
        console.log(`Original size: ${this.formatBytes(stats.originalSize)}`);
        console.log(`Compressed size: ${this.formatBytes(stats.compressedSize)}`);
        console.log(`Total saved: ${this.formatBytes(stats.savedBytes)} (${totalSavedPercentage}%)`);
        console.log(`Output directory: ${this.config.outputDir}`);
        console.log(`Backup directory: ${this.config.backupDir}`);

        if (stats.errors > 0) {
            console.log(`\n⚠️  ${stats.errors} images had errors during compression`);
        }

        if (stats.processed > 0) {
            console.log('\n✅ Image compression completed successfully!');
            console.log('\n💡 USAGE TIPS:');
            console.log('   • Use WebP format for modern browsers');
            console.log('   • Use AVIF format for maximum compression');
            console.log('   • Implement responsive images with srcset attribute');
            console.log('   • Consider lazy loading for better performance');
        }
    }
}

// Run the compressor if called directly
if (require.main === module) {
    const compressor = new ImageCompressor();
    compressor.run().catch(error => {
        console.error('💥 Image compression failed:', error);
        process.exit(1);
    });
}

module.exports = ImageCompressor;
