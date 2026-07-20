const { getDefaultConfig } = require('expo/metro-config');
const { withNativewind } = require('nativewind/metro');

const config = getDefaultConfig(__dirname);

// Reanimated worklets need lazy imports — keep this (#9445)
config.transformer.getTransformOptions = async () => ({
  transform: { inlineRequires: true },
});

// Wrap with NativeWind — per official docs, only 2 options exist in v5:
const nwConfig = withNativewind(config, {
  globalClassNamePolyfill: false,
  typescriptEnvPath: 'nativewind-env.d.ts',
});

// SAFETY: re-assert getTransformOptions in case withNativewind overwrote it
if (!nwConfig.transformer.getTransformOptions) {
  nwConfig.transformer.getTransformOptions = config.transformer.getTransformOptions;
}

module.exports = nwConfig;
