/**
 * ==========================================================================
 * IMAGE OPTIMIZATION SCRIPT
 * ==========================================================================
 * Advanced image optimization with WebP and AVIF support
 * Compresses images and generates multiple formats for performance
 * ==========================================================================
 */

const sharp = require('sharp');
const fs = require('fs').promises;
const path = require('path');
const glob = require('glob').glob;

// Configuration
const CONFIG = {
    inputDir: 'static/images',
    outputDir: 'static/images/optimized',
    formats: ['webp', 'avif', 'jpeg'],
    qualities: {
        webp: 80,
        avif: 75,
        jpeg: 85,
        png: 90
    },
    sizes: [
        { suffix: '', width: 2000, height: 2000 },
        { suffix: '_large', width: 1200, height: 1200 },
        { suffix: '_medium', width: 800, height: 800 },
        { suffix: '_small', width: 400, height: 400 },
        { suffix: '_thumb', width: 200, height: 200 }
    ]
};

/**
 * Optimize a single image file
 */
async function optimizeImage(inputPath, outputDir) {
    try {
        const filename = path.basename(inputPath, path.extname(inputPath));
        const originalSize = (await fs.stat(inputPath)).size;
        
        console.log(`📸 Processing: ${filename}`);
        
        const image = sharp(inputPath);
        const metadata = await image.metadata();
        
        let totalSaved = 0;
        let filesGenerated = 0;
        
        // Generate different sizes and formats
        for (const size of CONFIG.sizes) {
            for (const format of CONFIG.formats) {
                const outputFilename = `${filename}${size.suffix}.${format}`;
                const outputPath = path.join(outputDir, outputFilename);
                
                let pipeline = image.clone();
                
                // Resize if needed
                if (metadata.width > size.width || metadata.height > size.height) {
                    pipeline = pipeline.resize(size.width, size.height, {
                        fit: 'inside',
                        withoutEnlargement: true
                    });
                }
                
                // Apply format-specific optimizations
                switch (format) {
                    case 'webp':
                        pipeline = pipeline.webp({
                            quality: CONFIG.qualities.webp,
                            effort: 6
                        });
                        break;
                    case 'avif':
                        pipeline = pipeline.avif({
                            quality: CONFIG.qualities.avif,
                            effort: 9
                        });
                        break;
                    case 'jpeg':
                        pipeline = pipeline.jpeg({
                            quality: CONFIG.qualities.jpeg,
                            progressive: true,
                            mozjpeg: true
                        });
                        break;
                    case 'png':
                        pipeline = pipeline.png({
                            quality: CONFIG.qualities.png,
                            compressionLevel: 9
                        });
                        break;
                }
                
                await pipeline.toFile(outputPath);
                
                const optimizedSize = (await fs.stat(outputPath)).size;
                totalSaved += Math.max(0, originalSize - optimizedSize);
                filesGenerated++;
            }
        }
        
        const savedPercentage = ((totalSaved / (originalSize * filesGenerated)) * 100).toFixed(1);
        console.log(`✅ ${filename}: Generated ${filesGenerated} variants, saved ${savedPercentage}%`);
        
        return { originalSize, totalSaved, filesGenerated };
        
    } catch (error) {
        console.error(`❌ Error processing ${inputPath}:`, error.message);
        return { originalSize: 0, totalSaved: 0, filesGenerated: 0 };
    }
}

/**
 * Generate responsive image HTML
 */
function generateResponsiveImageHTML(filename, alt = '', className = '') {
    const baseName = path.basename(filename, path.extname(filename));
    
    return `
<!-- Responsive Image: ${filename} -->
<picture class="${className}">
    <source 
        media="(max-width: 400px)" 
        srcset="/static/images/optimized/${baseName}_small.avif" 
        type="image/avif">
    <source 
        media="(max-width: 400px)" 
        srcset="/static/images/optimized/${baseName}_small.webp" 
        type="image/webp">
    <source 
        media="(max-width: 800px)" 
        srcset="/static/images/optimized/${baseName}_medium.avif" 
        type="image/avif">
    <source 
        media="(max-width: 800px)" 
        srcset="/static/images/optimized/${baseName}_medium.webp" 
        type="image/webp">
    <source 
        media="(max-width: 1200px)" 
        srcset="/static/images/optimized/${baseName}_large.avif" 
        type="image/avif">
    <source 
        media="(max-width: 1200px)" 
        srcset="/static/images/optimized/${baseName}_large.webp" 
        type="image/webp">
    <source 
        srcset="/static/images/optimized/${baseName}.avif" 
        type="image/avif">
    <source 
        srcset="/static/images/optimized/${baseName}.webp" 
        type="image/webp">
    <img 
        src="/static/images/optimized/${baseName}.jpeg" 
        alt="${alt}" 
        loading="lazy"
        decoding="async">
</picture>
    `.trim();
}

/**
 * Create font optimization configuration
 */
function generateFontOptimization() {
    return {
        preload: [
            // Core fonts that should be preloaded
            '/static/fonts/inter-var.woff2',
            '/static/fonts/jetbrains-mono-var.woff2'
        ],
        fallbacks: {
            'Inter': 'system-ui, -apple-system, "Segoe UI", sans-serif',
            'JetBrains Mono': 'ui-monospace, "Cascadia Code", "Source Code Pro", Consolas, monospace'
        },
        display: 'swap' // Use font-display: swap for better performance
    };
}

/**
 * Main optimization function
 */
async function main() {
    console.log('🚀 Starting image optimization...\n');
    
    try {
        // Create output directory
        await fs.mkdir(CONFIG.outputDir, { recursive: true });
        
        // Find all image files
        const imagePatterns = [
            `${CONFIG.inputDir}/**/*.jpg`,
            `${CONFIG.inputDir}/**/*.jpeg`, 
            `${CONFIG.inputDir}/**/*.png`,
            `${CONFIG.inputDir}/**/*.gif`,
            `${CONFIG.inputDir}/**/*.bmp`,
            `${CONFIG.inputDir}/**/*.tiff`
        ];
        
        const imageFiles = [];
        for (const pattern of imagePatterns) {
            const files = await glob(pattern);
            imageFiles.push(...files);
        }
        
        if (imageFiles.length === 0) {
            console.log(`📂 No images found in ${CONFIG.inputDir}`);
            console.log('   Creating sample optimization structure...');
            
            // Create sample directory structure and documentation
            await fs.mkdir(CONFIG.inputDir, { recursive: true });
            
            const readmeContent = `# Image Optimization

This directory contains original images that will be optimized by the build process.

## Supported formats:
- JPG/JPEG
- PNG
- GIF
- BMP
- TIFF

## Output formats generated:
- WebP (modern browsers)
- AVIF (newest browsers)  
- JPEG (fallback)

## Generated sizes:
- Original (max 2000px)
- Large (1200px)
- Medium (800px)
- Small (400px)
- Thumbnail (200px)

## Usage:
Place your images in this directory and run:
\`\`\`bash
npm run optimize:images
\`\`\`

## HTML Usage:
Use the responsive image template in templates/components/responsive_image.html
`;
            
            await fs.writeFile(path.join(CONFIG.inputDir, 'README.md'), readmeContent);
            return;
        }
        
        console.log(`📦 Found ${imageFiles.length} images to optimize\n`);
        
        let totalStats = {
            originalSize: 0,
            totalSaved: 0,
            filesGenerated: 0
        };
        
        // Process images in parallel (but limit concurrency)
        const BATCH_SIZE = 3;
        for (let i = 0; i < imageFiles.length; i += BATCH_SIZE) {
            const batch = imageFiles.slice(i, i + BATCH_SIZE);
            const results = await Promise.all(
                batch.map(file => optimizeImage(file, CONFIG.outputDir))
            );
            
            // Aggregate stats
            results.forEach(result => {
                totalStats.originalSize += result.originalSize;
                totalStats.totalSaved += result.totalSaved;
                totalStats.filesGenerated += result.filesGenerated;
            });
        }
        
        // Generate optimization report
        const reportPath = path.join(CONFIG.outputDir, 'optimization-report.json');
        const report = {
            timestamp: new Date().toISOString(),
            input_directory: CONFIG.inputDir,
            output_directory: CONFIG.outputDir,
            images_processed: imageFiles.length,
            total_variants_generated: totalStats.filesGenerated,
            original_size_mb: (totalStats.originalSize / 1024 / 1024).toFixed(2),
            total_saved_mb: (totalStats.totalSaved / 1024 / 1024).toFixed(2),
            config: CONFIG,
            font_optimization: generateFontOptimization()
        };
        
        await fs.writeFile(reportPath, JSON.stringify(report, null, 2));
        
        // Generate responsive image template
        const templateHTML = `{% comment %}
Responsive Image Template
Usage: {% include 'components/responsive_image.html' with filename='hero.jpg' alt='Hero image' class='w-full h-64 object-cover' %}
{% endcomment %}

<picture class="{{ class|default:'' }}">
    <source 
        media="(max-width: 400px)" 
        srcset="{% get_static_prefix %}images/optimized/{{ filename|cut:'.jpg'|cut:'.jpeg'|cut:'.png' }}_small.avif" 
        type="image/avif">
    <source 
        media="(max-width: 400px)" 
        srcset="{% get_static_prefix %}images/optimized/{{ filename|cut:'.jpg'|cut:'.jpeg'|cut:'.png' }}_small.webp" 
        type="image/webp">
    <source 
        media="(max-width: 800px)" 
        srcset="{% get_static_prefix %}images/optimized/{{ filename|cut:'.jpg'|cut:'.jpeg'|cut:'.png' }}_medium.avif" 
        type="image/avif">
    <source 
        media="(max-width: 800px)" 
        srcset="{% get_static_prefix %}images/optimized/{{ filename|cut:'.jpg'|cut:'.jpeg'|cut:'.png' }}_medium.webp" 
        type="image/webp">
    <source 
        media="(max-width: 1200px)" 
        srcset="{% get_static_prefix %}images/optimized/{{ filename|cut:'.jpg'|cut:'.jpeg'|cut:'.png' }}_large.avif" 
        type="image/avif">
    <source 
        media="(max-width: 1200px)" 
        srcset="{% get_static_prefix %}images/optimized/{{ filename|cut:'.jpg'|cut:'.jpeg'|cut:'.png' }}_large.webp" 
        type="image/webp">
    <source 
        srcset="{% get_static_prefix %}images/optimized/{{ filename|cut:'.jpg'|cut:'.jpeg'|cut:'.png' }}.avif" 
        type="image/avif">
    <source 
        srcset="{% get_static_prefix %}images/optimized/{{ filename|cut:'.jpg'|cut:'.jpeg'|cut:'.png' }}.webp" 
        type="image/webp">
    <img 
        src="{% get_static_prefix %}images/optimized/{{ filename|cut:'.jpg'|cut:'.jpeg'|cut:'.png' }}.jpeg" 
        alt="{{ alt|default:'' }}" 
        loading="lazy"
        decoding="async"
        class="{{ class|default:'' }}">
</picture>`;
        
        await fs.mkdir('templates/components', { recursive: true });
        await fs.writeFile('templates/components/responsive_image.html', templateHTML);
        
        // Final summary
        console.log('\n🎉 Optimization Complete!');
        console.log(`📊 Processed: ${imageFiles.length} images`);
        console.log(`📁 Generated: ${totalStats.filesGenerated} optimized variants`);
        console.log(`💾 Original size: ${(totalStats.originalSize / 1024 / 1024).toFixed(2)} MB`);
        console.log(`✨ Space saved: ${(totalStats.totalSaved / 1024 / 1024).toFixed(2)} MB`);
        console.log(`📄 Report: ${reportPath}`);
        console.log(`🎨 Template: templates/components/responsive_image.html`);
        
    } catch (error) {
        console.error('❌ Optimization failed:', error);
        process.exit(1);
    }
}

// Run the optimization
if (require.main === module) {
    main();
}

module.exports = { optimizeImage, generateResponsiveImageHTML, generateFontOptimization };