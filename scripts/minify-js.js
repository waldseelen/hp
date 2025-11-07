#!/usr/bin/env node

const fs = require('fs').promises;
const path = require('path');
const { minify } = require('terser');

async function minifyFile(inputPath, outputPath) {
    try {
        const code = await fs.readFile(inputPath, 'utf8');
        const result = await minify(code, {
            sourceMap: {
                filename: path.basename(outputPath),
                url: `${path.basename(outputPath)}.map`
            },
            compress: {
                drop_console: false,
                drop_debugger: true,
                pure_funcs: ['console.log']
            },
            mangle: {
                keep_fnames: false
            },
            format: {
                comments: false
            }
        });

        await fs.writeFile(outputPath, result.code);

        if (result.map) {
            await fs.writeFile(`${outputPath}.map`, result.map);
        }

        const originalSize = (await fs.stat(inputPath)).size;
        const minifiedSize = result.code.length;
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
        } else if (item.isFile() && item.name.endsWith('.js') && !item.name.endsWith('.min.js')) {
            const outputPath = fullPath.replace('.js', '.min.js');
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
        console.log('Starting JavaScript minification...');
        const stats = await processDirectory(staticDir);

        const totalCompression = stats.totalOriginal > 0
            ? ((stats.totalOriginal - stats.totalMinified) / stats.totalOriginal * 100).toFixed(1)
            : 0;

        console.log(`\n=== JavaScript Minification Complete ===`);
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
