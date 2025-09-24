const path = require('path');

module.exports = {
  mode: process.env.NODE_ENV === 'production' ? 'production' : 'development',

  entry: {
    // Core bundle - essential functionality
    core: {
      import: [
        './static/js/core/theme-handler.js',
        './static/js/ui-shell.js'
      ],
      priority: 'high'
    },

    // Main UI bundle - primary user interface
    main: {
      import: './static/js/ui-enhancements.js',
      dependOn: 'core',
      priority: 'medium'
    },

    // Analytics bundle - tracking and monitoring
    analytics: {
      import: [
        './static/js/analytics.js',
        './static/js/performance.min.js'
      ],
      priority: 'low'
    },

    // Animation bundle - non-critical animations
    animations: {
      import: [
        './static/js/modules/animations.js',
        './static/js/modules/scroll-animations.js',
        './static/js/modules/parallax.js',
        './static/js/modules/cursor.js'
      ],
      priority: 'low'
    },

    // Components bundle - specialized components
    components: {
      import: [
        './static/js/components/privacy-settings.js',
        './static/js/components/pwa.js',
        './static/js/search-autocomplete.js'
      ],
      priority: 'medium'
    }
  },

  output: {
    path: path.resolve(__dirname, 'static/js/dist'),
    filename: ({ chunk }) => {
      const priority = chunk.name === 'core' ? 'high' :
                     chunk.name === 'main' || chunk.name === 'components' ? 'medium' : 'low';
      return `[name].${priority}.bundle.js`;
    },
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

    usedExports: true,
    sideEffects: false,

    // Minimize in production
    minimize: process.env.NODE_ENV === 'production'
  },

  resolve: {
    extensions: ['.js'],
    alias: {
      '@': path.resolve(__dirname, 'static/js'),
      '@components': path.resolve(__dirname, 'static/js/components'),
      '@modules': path.resolve(__dirname, 'static/js/modules')
    }
  },

  devtool: process.env.NODE_ENV === 'production' ? 'source-map' : 'eval-source-map',

  stats: {
    assets: true,
    chunks: true,
    modules: false,
    entrypoints: true,
    performance: true
  }
};