#!/usr/bin/env node
/**
 * JAVASCRIPT MINIFICATION SCRIPT
 * ==============================
 * 
 * Advanced JavaScript minification and optimization tool for Django portfolio project.
 * Uses Terser for modern ES6+ minification with source maps and optimization.
 * 
 * FEATURES:
 * - Minifies all JS files in static/js/
 * - Creates .min.js versions with source maps
 * - Preserves original files
 * - Compression statistics
 * - Error handling and logging
 * - Skip already minified files
 * 
 * USAGE:
 *   node scripts/minify-js.js
 *   npm run minify:js
 */

const fs = require('fs');
const path = require('path');
const { minify } = require('terser');
const { glob } = require('glob');

class JSMinifier {
    constructor() {
        this.config = {
            sourceDir: 'static/js',
            outputDir: 'static/js/minified',
            sourceMap: true,
            stats: {
                processed: 0,
                errors: 0,
                originalSize: 0,
                minifiedSize: 0,
                savedBytes: 0
            }
        };
        
        this.terserOptions = {
            compress: {
                drop_console: true,
                drop_debugger: true,
                pure_funcs: ['console.log', 'console.warn'],
                passes: 2
            },
            mangle: {
                toplevel: false,
                keep_fnames: false,
                reserved: ['$', 'jQuery', 'django']
            },
            format: {
                comments: false,
                beautify: false
            },
            sourceMap: this.config.sourceMap ? {
                filename: undefined, // Will be set per file
                url: undefined,      // Will be set per file  
                includeSources: true
            } : false
        };
    }

    async initialize() {
        console.log('🔧 JavaScript Minification Started');
        console.log('=====================================');
        
        // Create output directory
        if (!fs.existsSync(this.config.outputDir)) {
            fs.mkdirSync(this.config.outputDir, { recursive: true });
            console.log(`📁 Created output directory: ${this.config.outputDir}`);
        }
    }

    async findJSFiles() {
        const patterns = [
            `${this.config.sourceDir}/*.js`,
            `${this.config.sourceDir}/**/*.js`
        ];
        
        let files = [];
        for (const pattern of patterns) {
            const matches = glob.sync(pattern, {
                ignore: [
                    '**/*.min.js',
                    '**/minified/**',
                    '**/node_modules/**'
                ]
            });
            files = files.concat(matches);
        }
        
        // Remove duplicates
        return [...new Set(files)];
    }

    async minifyFile(filePath) {
        try {
            const fileName = path.basename(filePath, '.js');
            const relativeDir = path.relative(this.config.sourceDir, path.dirname(filePath));
            const outputPath = path.join(this.config.outputDir, relativeDir, `${fileName}.min.js`);
            const sourceMapPath = `${outputPath}.map`;
            
            // Read source file
            const sourceCode = fs.readFileSync(filePath, 'utf8');
            const originalSize = Buffer.byteLength(sourceCode, 'utf8');
            
            // Configure terser options for this file
            const options = { ...this.terserOptions };
            if (options.sourceMap) {
                options.sourceMap.filename = path.basename(outputPath);
                options.sourceMap.url = `${path.basename(outputPath)}.map`;
            }
            
            // Minify
            const result = await minify(sourceCode, options);
            
            if (result.error) {
                throw result.error;
            }
            
            // Create output directory if needed
            const outputDirPath = path.dirname(outputPath);
            if (!fs.existsSync(outputDirPath)) {
                fs.mkdirSync(outputDirPath, { recursive: true });
            }
            
            // Write minified file
            let minifiedCode = result.code;
            if (result.map) {
                minifiedCode += `\n//# sourceMappingURL=${path.basename(sourceMapPath)}`;
                fs.writeFileSync(sourceMapPath, result.map);
            }
            
            fs.writeFileSync(outputPath, minifiedCode);
            
            // Calculate savings
            const minifiedSize = Buffer.byteLength(minifiedCode, 'utf8');
            const savedBytes = originalSize - minifiedSize;
            const savedPercentage = ((savedBytes / originalSize) * 100).toFixed(1);
            
            // Update statistics
            this.config.stats.processed++;
            this.config.stats.originalSize += originalSize;
            this.config.stats.minifiedSize += minifiedSize;
            this.config.stats.savedBytes += savedBytes;
            
            console.log(`✅ ${filePath}`);
            console.log(`   → ${outputPath}`);
            console.log(`   📊 ${this.formatBytes(originalSize)} → ${this.formatBytes(minifiedSize)} (${savedPercentage}% saved)`);
            
            if (result.map) {
                console.log(`   🗺️  Source map: ${sourceMapPath}`);
            }
            
            return {
                success: true,
                originalSize,
                minifiedSize,
                savedBytes,
                savedPercentage
            };
            
        } catch (error) {
            this.config.stats.errors++;
            console.error(`❌ Error minifying ${filePath}:`);
            console.error(`   ${error.message}`);
            
            return {
                success: false,
                error: error.message
            };
        }
    }

    formatBytes(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    async run() {
        await this.initialize();
        
        const jsFiles = await this.findJSFiles();
        
        if (jsFiles.length === 0) {
            console.log('⚠️  No JavaScript files found to minify');
            return;
        }
        
        console.log(`📦 Found ${jsFiles.length} JavaScript files to process\n`);
        
        // Process each file
        for (const file of jsFiles) {
            await this.minifyFile(file);
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
        
        console.log('📊 MINIFICATION SUMMARY');
        console.log('========================');
        console.log(`Files processed: ${stats.processed}`);
        console.log(`Errors: ${stats.errors}`);
        console.log(`Original size: ${this.formatBytes(stats.originalSize)}`);
        console.log(`Minified size: ${this.formatBytes(stats.minifiedSize)}`);
        console.log(`Total saved: ${this.formatBytes(stats.savedBytes)} (${totalSavedPercentage}%)`);
        console.log(`Output directory: ${this.config.outputDir}`);
        
        if (stats.errors > 0) {
            console.log(`\n⚠️  ${stats.errors} files had errors during minification`);
        }
        
        if (stats.processed > 0) {
            console.log('\n✅ JavaScript minification completed successfully!');
        }
    }
}

// Run the minifier if called directly
if (require.main === module) {
    const minifier = new JSMinifier();
    minifier.run().catch(error => {
        console.error('💥 Minification failed:', error);
        process.exit(1);
    });
}

module.exports = JSMinifier;