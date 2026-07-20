const { getDefaultConfig } = require('expo/metro-config');

const config = getDefaultConfig(__dirname);

// Fix: Reanimated worklets need lazy imports — Expo eager-loads by default
// Without this, workletsModuleProxy is undefined and app crashes on startup (#9445)
config.transformer.getTransformOptions = async () => ({
  transform: {
    inlineRequires: true,
  },
});

module.exports = config;
