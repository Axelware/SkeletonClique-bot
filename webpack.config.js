const path = require('path');

module.exports = {
  mode: 'production',
  entry: './Semi Botomatic/cogs/web/static/src/timezones.js',
  output: {
    path: path.resolve(__dirname, 'Semi Botomatic/cogs/web/static/'),
    filename: 'bundle.js'
  }
};