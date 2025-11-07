#!/usr/bin/env node

const fs = require('fs').promises;
const path = require('path');
const postcss = require('postcss');
const cssnano = require('cssnano');
const autoprefixer = require('autoprefixer');

async function minifyFile(inputPath, outputPath) {
    try {
        const css = await fs.readFile(inputPath, 'utf8');

        const result = await postcss([
            autoprefixer,
            cssnano({
                preset: ['default', {
                    discardComments: { removeAll: true },
                    normalizeWhitespace: true,
                    mergeLonghand: true,
                    mergeRules: true
                }]
            })
        ]).process(css, {
            from: inputPath,
            to: outputPath,
            map: { inline: false }
        });

        await fs.writeFile(outputPath, result.css);

        if (result.map) {
            await fs.writeFile(`${outputPath}.map`, result.map.toString());
        }

        const originalSize = (await fs.stat(inputPath)).size;
        const minifiedSize = result.css.length;
        const compression = ((originalSize - minifiedSize) / originalSize * 100).toFixed(1);

        console.log(`Minified: ${inputPath} -> ${outputPath} (${compression}% compression)`);

        return { originalSize, minifiedSize, compression };
    } catch (error) {
        console.error(`Error minifying ${inputPath}:`, error.message);
        return null;
    }
}

async function processDirectory(dir) {
    const items = await fs.readdir(dir, { withFileTypes: true });
    const stats = { totalOriginal: 0, totalMinified: 0, files: 0 };

    for (const item of items) {
        const fullPath = path.join(dir, item.name);

        if (item.isDirectory() && !item.name.includes('node_modules') && !item.name.includes('.git')) {
            const subStats = await processDirectory(fullPath);
            stats.totalOriginal += subStats.totalOriginal;
            stats.totalMinified += subStats.totalMinified;
            stats.files += subStats.files;
        } else if (item.isFile() && item.name.endsWith('.css') && !item.name.endsWith('.min.css')) {
            const outputPath = fullPath.replace('.css', '.min.css');
            const result = await minifyFile(fullPath, outputPath);

            if (result) {
                stats.totalOriginal += result.originalSize;
                stats.totalMinified += result.minifiedSize;
                stats.files++;
            }
        }
    }

    return stats;
}

async function main() {
    const staticDir = path.join(__dirname, '..', 'static');

    try {
        console.log('Starting CSS minification...');
        const stats = await processDirectory(staticDir);

        const totalCompression = stats.totalOriginal > 0
            ? ((stats.totalOriginal - stats.totalMinified) / stats.totalOriginal * 100).toFixed(1)
            : 0;

        console.log(`\n=== CSS Minification Complete ===`);
        console.log(`Files processed: ${stats.files}`);
        console.log(`Original size: ${(stats.totalOriginal / 1024).toFixed(1)} KB`);
        console.log(`Minified size: ${(stats.totalMinified / 1024).toFixed(1)} KB`);
        console.log(`Total compression: ${totalCompression}%`);

    } catch (error) {
        console.error('Error during minification:', error);
        process.exit(1);
    }
}

if (require.main === module) {
    main();
}
