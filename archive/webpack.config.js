const path = require('path');
const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer');
const TerserPlugin = require('terser-webpack-plugin');

module.exports = {
    mode: process.env.NODE_ENV === 'production' ? 'production' : 'development',

    entry: {
        // Core bundle - essential functionality
        core: {
            import: [
                './static/js/core/theme-handler.js',
                './static/js/ui-shell.js'
            ]
        },

        // Main UI bundle - primary user interface
        main: {
            import: './static/js/ui-enhancements.js',
            dependOn: 'core'
        },

        // Analytics bundle - tracking and monitoring
        analytics: {
            import: [
                './static/js/analytics.js',
                './static/js/performance.min.js'
            ]
        },

        // Animation bundle - non-critical animations
        animations: {
            import: [
                './static/js/modules/animations.js',
                './static/js/modules/scroll-animations.js',
                './static/js/modules/parallax.js',
                './static/js/modules/cursor.js'
            ]
        },

        // Components bundle - specialized components
        components: {
            import: [
                './static/js/components/privacy-settings.js',
                './static/js/components/pwa.js',
                './static/js/search-autocomplete.js'
            ]
        }
    }, output: {
        path: path.resolve(__dirname, 'static/js/dist'),
        filename: '[name].bundle.js',
        chunkFilename: '[name].[contenthash:8].chunk.js',
        clean: true,
        publicPath: '/static/js/dist/'
    },

    module: {
        rules: [
            {
                test: /\.js$/,
                exclude: /node_modules/,
                use: {
                    loader: 'babel-loader',
                    options: {
                        presets: [
                            ['@babel/preset-env', {
                                targets: {
                                    browsers: ['> 1%', 'last 2 versions', 'not dead']
                                },
                                modules: false,
                                useBuiltIns: 'usage',
                                corejs: 3
                            }]
                        ]
                    }
                }
            }
        ]
    },

    optimization: {
        splitChunks: {
            chunks: 'all',
            maxInitialRequests: 25,
            maxAsyncRequests: 30,
            minSize: 20000,
            maxSize: 244000,
            cacheGroups: {
                vendor: {
                    test: /[\\/]node_modules[\\/]/,
                    name: 'vendors',
                    priority: 10,
                    reuseExistingChunk: true
                },
                common: {
                    name: 'common',
                    minChunks: 2,
                    priority: 5,
                    reuseExistingChunk: true
                }
            }
        },

        runtimeChunk: 'single',
        usedExports: true,
        sideEffects: false,

        // Minimize in production with TerserPlugin
        minimize: process.env.NODE_ENV === 'production',
        minimizer: [
            new TerserPlugin({
                terserOptions: {
                    compress: {
                        drop_console: process.env.NODE_ENV === 'production',
                        drop_debugger: true,
                        pure_funcs: ['console.log', 'console.info'],
                        passes: 2
                    },
                    mangle: {
                        safari10: true
                    },
                    format: {
                        comments: false,
                        ascii_only: true
                    }
                },
                extractComments: false,
                parallel: true
            })
        ]
    },

    resolve: {
        extensions: ['.js'],
        alias: {
            '@': path.resolve(__dirname, 'static/js'),
            '@components': path.resolve(__dirname, 'static/js/components'),
            '@modules': path.resolve(__dirname, 'static/js/modules')
        }
    },

    plugins: [
        ...(process.env.ANALYZE ? [new BundleAnalyzerPlugin({
            analyzerMode: process.env.CI ? 'static' : 'server',
            reportFilename: 'bundle-report.html',
            openAnalyzer: !process.env.CI,
            generateStatsFile: true,
            statsFilename: 'bundle-stats.json'
        })] : [])
    ], devtool: process.env.NODE_ENV === 'production' ? 'source-map' : 'eval-source-map',

    stats: {
        assets: true,
        chunks: true,
        modules: false,
        entrypoints: true,
        performance: true
    }
};
