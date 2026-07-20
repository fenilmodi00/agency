import React from 'react';
import Animated from 'react-native-reanimated';
import { YStack, type ColorTokens, type RadiusTokens, type SpaceTokens } from 'tamagui';
import { useEntranceAnimation, usePressAnimation } from '@/hooks/useClayAnimations';

interface ClayAnimatedCardProps {
  children: React.ReactNode;
  onPress?: () => void;
  delay?: number;
  backgroundColor?: ColorTokens;
  borderRadius?: RadiusTokens;
  padding?: SpaceTokens;
  borderWidth?: number;
  borderColor?: ColorTokens;
}

export function ClayAnimatedCard({
  children, onPress, delay = 0,
  backgroundColor = '$canvas', borderRadius = '$lg', padding = '$lg',
  borderWidth = 1, borderColor = '$hairline',
}: ClayAnimatedCardProps) {
  const { animatedStyle: entranceStyle } = useEntranceAnimation(delay);
  const { onPressIn, onPressOut, animatedStyle: pressStyle } = usePressAnimation(0.97);

  return (
    <Animated.View style={[entranceStyle, onPress ? pressStyle : undefined]}>
      <YStack
        background={backgroundColor}
        rounded={borderRadius}
        p={padding}
        borderWidth={borderWidth}
        borderColor={borderColor}
        onPress={onPress}
      >
        {children}
      </YStack>
    </Animated.View>
  );
}

export default ClayAnimatedCard;
