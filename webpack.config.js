// webpack.config.js
const path = require('path');

module.exports = {
  mode: 'production', // Change to 'development' for debugging if needed
  target: 'electron-renderer', // Specify Electron renderer process target
  entry: './src/index.jsx', // Adjust this path if your entry point is elsewhere
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: 'bundle.js'
  },
  resolve: {
    extensions: ['.js', '.jsx'],
    fallback: {
      "fs": false, // Do not bundle Node's fs (only available in main process)
      "path": require.resolve("path-browserify") // Polyfill for path
    }
  },
  module: {
    rules: [
      {
        test: /\.(js|jsx)$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: [
              '@babel/preset-env',
              '@babel/preset-react'
            ]
          }
        }
      }
    ]
  },
  externals: {
    // Let Electron's built-in modules be available at runtime
    "electron": "require('electron')"
  }
};
