import React, { useCallback } from 'react';
import { Pressable } from 'react-native';
import Animated from 'react-native-reanimated';
import { Text, YStack, Spinner, type ColorTokens } from 'tamagui';
import { usePressAnimation } from '@/hooks/useClayAnimations';

type ClayButtonVariant = 'primary' | 'secondary' | 'on-color' | 'text-link';

interface ClayAnimatedButtonProps {
  children: React.ReactNode;
  onPress: () => void;
  variant?: ClayButtonVariant;
  disabled?: boolean;
  loading?: boolean;
  fullWidth?: boolean;
  maxWidth?: number;
  height?: number;
}

const VARIANT_STYLES: Record<ClayButtonVariant, { bg: ColorTokens | 'transparent'; color: ColorTokens; border?: ColorTokens }> = {
  primary: { bg: '$primary', color: '$on-primary' },
  secondary: { bg: '$canvas', color: '$ink', border: '$hairline' },
  'on-color': { bg: '$on-primary', color: '$ink' },
  'text-link': { bg: 'transparent', color: '$ink' },
};

export function ClayAnimatedButton({
  children, onPress, variant = 'primary', disabled = false,
  loading = false, fullWidth = false, maxWidth, height = 44,
}: ClayAnimatedButtonProps) {
  const { onPressIn, onPressOut, animatedStyle } = usePressAnimation(0.96);
  const styles = VARIANT_STYLES[variant];

  const handlePress = useCallback(() => {
    if (!disabled && !loading) onPress();
  }, [disabled, loading, onPress]);

  return (
    <Pressable
      onPressIn={onPressIn}
      onPressOut={onPressOut}
      onPress={handlePress}
      disabled={disabled || loading}
      style={{ width: fullWidth ? '100%' : maxWidth ? maxWidth : undefined, opacity: disabled ? 0.5 : 1 }}
    >
      <Animated.View style={[animatedStyle]}>
        <YStack
          background={styles.bg}
          borderWidth={styles.border ? 1 : 0}
          borderColor={styles.border}
          rounded="$md"
          height={height}
          justify="center"
          items="center"
          px="$5"
          flexDirection="row"
          gap="$2"
        >
          {loading ? (
            <Spinner size="small" color={styles.color} />
          ) : (
            <Text color={styles.color} fontSize="$button" fontWeight="600" letterSpacing={0}>
              {children}
            </Text>
          )}
        </YStack>
      </Animated.View>
    </Pressable>
  );
}

export default ClayAnimatedButton;
