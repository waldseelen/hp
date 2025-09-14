#!/usr/bin/env node
/**
 * CSS MINIFICATION SCRIPT
 * ========================
 * 
 * Advanced CSS minification and optimization tool for Django portfolio project.
 * Uses CleanCSS for optimization with source maps and advanced features.
 * 
 * FEATURES:
 * - Minifies all CSS files in static/css/
 * - Creates .min.css versions
 * - Removes unused CSS (optional)
 * - Combines media queries
 * - Optimizes vendor prefixes
 * - Compression statistics
 * 
 * USAGE:
 *   node scripts/minify-css.js
 *   npm run minify:css
 */

const fs = require('fs');
const path = require('path');
const CleanCSS = require('clean-css');
const { glob } = require('glob');

class CSSMinifier {
    constructor() {
        this.config = {
            sourceDir: 'static/css',
            outputDir: 'static/css/minified',
            sourceMap: true,
            stats: {
                processed: 0,
                errors: 0,
                originalSize: 0,
                minifiedSize: 0,
                savedBytes: 0
            }
        };
        
        this.cleanCSSOptions = {
            level: 2, // Advanced optimizations
            sourceMap: this.config.sourceMap,
            format: 'beautify' === 'minify' ? false : {
                breaks: {
                    afterComment: false,
                    afterRuleBegins: false,
                    afterRuleEnds: false,
                    beforeBlockEnds: false,
                    betweenSelectors: false
                },
                indentBy: 0,
                indentWith: '',
                spaces: {
                    aroundSelectorRelation: false,
                    beforeBlockBegins: false,
                    beforeValue: false
                },
                wrapAt: false
            },
            inline: ['local'],
            rebase: false
        };
    }

    async initialize() {
        console.log('🎨 CSS Minification Started');
        console.log('============================');
        
        // Create output directory
        if (!fs.existsSync(this.config.outputDir)) {
            fs.mkdirSync(this.config.outputDir, { recursive: true });
            console.log(`📁 Created output directory: ${this.config.outputDir}`);
        }
    }

    async findCSSFiles() {
        const patterns = [
            `${this.config.sourceDir}/*.css`,
            `${this.config.sourceDir}/**/*.css`
        ];
        
        let files = [];
        for (const pattern of patterns) {
            const matches = glob.sync(pattern, {
                ignore: [
                    '**/*.min.css',
                    '**/minified/**',
                    '**/node_modules/**',
                    '**/purged/**',
                    '**/optimized/**/*.min.css'
                ]
            });
            files = files.concat(matches);
        }
        
        // Remove duplicates and filter out already optimized files
        return [...new Set(files)].filter(file => {
            const fileName = path.basename(file);
            return !fileName.includes('.min.') && !fileName.includes('optimized');
        });
    }

    async minifyFile(filePath) {
        try {
            const fileName = path.basename(filePath, '.css');
            const relativeDir = path.relative(this.config.sourceDir, path.dirname(filePath));
            const outputPath = path.join(this.config.outputDir, relativeDir, `${fileName}.min.css`);
            const sourceMapPath = `${outputPath}.map`;
            
            // Read source file
            const sourceCSS = fs.readFileSync(filePath, 'utf8');
            const originalSize = Buffer.byteLength(sourceCSS, 'utf8');
            
            // Initialize CleanCSS
            const cleanCSS = new CleanCSS(this.cleanCSSOptions);
            
            // Minify CSS
            const result = cleanCSS.minify(sourceCSS);
            
            if (result.errors && result.errors.length > 0) {
                throw new Error(result.errors.join(', '));
            }
            
            // Create output directory if needed
            const outputDirPath = path.dirname(outputPath);
            if (!fs.existsSync(outputDirPath)) {
                fs.mkdirSync(outputDirPath, { recursive: true });
            }
            
            // Write minified CSS
            let minifiedCSS = result.styles;
            
            // Add source map reference if enabled
            if (result.sourceMap && this.config.sourceMap) {
                minifiedCSS += `\n/*# sourceMappingURL=${path.basename(sourceMapPath)} */`;
                fs.writeFileSync(sourceMapPath, result.sourceMap.toString());
            }
            
            fs.writeFileSync(outputPath, minifiedCSS);
            
            // Calculate savings
            const minifiedSize = Buffer.byteLength(minifiedCSS, 'utf8');
            const savedBytes = originalSize - minifiedSize;
            const savedPercentage = originalSize > 0 ? ((savedBytes / originalSize) * 100).toFixed(1) : '0.0';
            
            // Update statistics
            this.config.stats.processed++;
            this.config.stats.originalSize += originalSize;
            this.config.stats.minifiedSize += minifiedSize;
            this.config.stats.savedBytes += savedBytes;
            
            console.log(`✅ ${filePath}`);
            console.log(`   → ${outputPath}`);
            console.log(`   📊 ${this.formatBytes(originalSize)} → ${this.formatBytes(minifiedSize)} (${savedPercentage}% saved)`);
            
            // Show optimization details
            if (result.stats && result.stats.efficiency) {
                console.log(`   ⚡ Efficiency: ${result.stats.efficiency.toFixed(1)}%`);
            }
            
            if (result.warnings && result.warnings.length > 0) {
                console.log(`   ⚠️  Warnings: ${result.warnings.length}`);
                result.warnings.forEach(warning => {
                    console.log(`      ${warning}`);
                });
            }
            
            if (result.sourceMap && this.config.sourceMap) {
                console.log(`   🗺️  Source map: ${sourceMapPath}`);
            }
            
            return {
                success: true,
                originalSize,
                minifiedSize,
                savedBytes,
                savedPercentage,
                warnings: result.warnings || []
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
        
        const cssFiles = await this.findCSSFiles();
        
        if (cssFiles.length === 0) {
            console.log('⚠️  No CSS files found to minify');
            return;
        }
        
        console.log(`📦 Found ${cssFiles.length} CSS files to process\n`);
        
        // Process each file
        const results = [];
        for (const file of cssFiles) {
            const result = await this.minifyFile(file);
            results.push(result);
            console.log(''); // Empty line for readability
        }
        
        // Print summary statistics
        this.printSummary(results);
    }

    printSummary(results) {
        const stats = this.config.stats;
        const totalSavedPercentage = stats.originalSize > 0 
            ? ((stats.savedBytes / stats.originalSize) * 100).toFixed(1)
            : '0.0';
        
        const successfulFiles = results.filter(r => r.success).length;
        const totalWarnings = results.reduce((sum, r) => sum + (r.warnings ? r.warnings.length : 0), 0);
        
        console.log('📊 CSS MINIFICATION SUMMARY');
        console.log('============================');
        console.log(`Files processed: ${stats.processed}`);
        console.log(`Successful: ${successfulFiles}`);
        console.log(`Errors: ${stats.errors}`);
        console.log(`Warnings: ${totalWarnings}`);
        console.log(`Original size: ${this.formatBytes(stats.originalSize)}`);
        console.log(`Minified size: ${this.formatBytes(stats.minifiedSize)}`);
        console.log(`Total saved: ${this.formatBytes(stats.savedBytes)} (${totalSavedPercentage}%)`);
        console.log(`Output directory: ${this.config.outputDir}`);
        
        if (stats.errors > 0) {
            console.log(`\n⚠️  ${stats.errors} files had errors during minification`);
        }
        
        if (totalWarnings > 0) {
            console.log(`\n⚠️  ${totalWarnings} warnings generated during minification`);
        }
        
        if (stats.processed > 0) {
            console.log('\n✅ CSS minification completed successfully!');
            
            // Performance tips
            if (totalSavedPercentage < 20) {
                console.log('\n💡 TIP: Consider enabling CSS purging to remove unused styles');
            }
            if (stats.originalSize > 1024 * 1024) { // > 1MB
                console.log('\n💡 TIP: Consider splitting large CSS files for better caching');
            }
        }
    }
}

// Run the minifier if called directly
if (require.main === module) {
    const minifier = new CSSMinifier();
    minifier.run().catch(error => {
        console.error('💥 CSS minification failed:', error);
        process.exit(1);
    });
}

module.exports = CSSMinifier;