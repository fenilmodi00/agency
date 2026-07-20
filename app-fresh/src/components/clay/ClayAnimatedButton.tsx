import React, { useCallback } from 'react';
import { Pressable, ActivityIndicator } from 'react-native';
import Animated from 'react-native-reanimated';
import { View, Text } from '@/tw';
import { cn, clayButtonBase } from '@/tw/cn';
import { usePressAnimation } from '@/hooks/useClayAnimations';

type Variant = 'primary' | 'secondary' | 'on-color' | 'text-link';

const VARIANT_BG: Record<Variant, string> = {
  primary: 'bg-primary',
  secondary: 'bg-canvas border border-hairline',
  'on-color': 'bg-on-primary',
  'text-link': 'bg-transparent',
};
const VARIANT_TEXT: Record<Variant, string> = {
  primary: 'text-on-primary',
  secondary: 'text-ink',
  'on-color': 'text-ink',
  'text-link': 'text-ink',
};
const VARIANT_SPINNER: Record<Variant, string> = {
  primary: 'text-on-primary', secondary: 'text-ink',
  'on-color': 'text-ink', 'text-link': 'text-ink',
};

export function ClayAnimatedButton({
  children, onPress, variant = 'primary', disabled = false,
  loading = false, fullWidth = false, maxWidth, height = 44,
}: {
  children: React.ReactNode; onPress: () => void; variant?: Variant;
  disabled?: boolean; loading?: boolean; fullWidth?: boolean; maxWidth?: number; height?: number;
}) {
  const { onPressIn, onPressOut, animatedStyle } = usePressAnimation(0.96);
  const handlePress = useCallback(() => {
    if (!disabled && !loading) onPress();
  }, [disabled, loading, onPress]);

  return (
    <Pressable
      onPressIn={onPressIn} onPressOut={onPressOut} onPress={handlePress}
      disabled={disabled || loading}
      style={{ width: fullWidth ? '100%' : maxWidth ?? undefined, opacity: disabled ? 0.5 : 1 }}
    >
      <Animated.View style={[animatedStyle]}>
        <View className={cn(clayButtonBase, VARIANT_BG[variant])} style={{ height }}>
          {loading ? (
            <ActivityIndicator size="small" className={VARIANT_SPINNER[variant]} />
          ) : (
            <Text className={cn('text-button font-semibold', VARIANT_TEXT[variant])}>{children}</Text>
          )}
        </View>
      </Animated.View>
    </Pressable>
  );
}
export default ClayAnimatedButton;
