const config = require('@kubosho/configs/textlint');

module.exports = {
  ...config,
  rules: {
    ...config.rules,
    'no-dead-link': false,
    'preset-jtf-style': {
      '1.1.3.箇条書き': false,
      '3.1.2.全角文字どうし': false,
    },
  },
};
