import { Platform } from 'react-native';

/**
 * Whether react-native-reanimated is available on the current platform.
 * On web, Reanimated v4.1.1 may crash with "createSerializableObject should never be called in JSWorklets" (#8285).
 * This guard allows components to fall back to static rendering on web.
 */
export const IS_REANIMATED_AVAILABLE = Platform.OS !== 'web';

/**
 * Re-exports Reanimated APIs only on native platforms.
 * On web, exports no-op fallbacks to prevent import-time crashes.
 */
export const Reanimated = IS_REANIMATED_AVAILABLE
  ? require('react-native-reanimated')
  : {
      View: require('react-native').View,
      Text: require('react-native').Text,
      useSharedValue: (v: any) => ({ value: v }),
      useAnimatedStyle: () => ({}),
      useAnimatedScrollHandler: () => ({}),
      withTiming: (v: any) => v,
      withSpring: (v: any) => v,
      withSequence: (...args: any[]) => args[0],
      withRepeat: (v: any) => v,
      withDelay: (_d: any, v: any) => v,
      Easing: { linear: () => {} },
    };
