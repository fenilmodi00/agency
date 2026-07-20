import React, { useEffect } from 'react';
import Animated, { useSharedValue, useAnimatedStyle, withRepeat, withTiming, Easing } from 'react-native-reanimated';
import { YStack, Text, useTheme } from 'tamagui';

interface ClaySpinnerProps {
  size?: number;
  colorToken?: string;
  label?: string;
  labelColorToken?: string;
}

export function ClaySpinner({
  size = 40, colorToken = '$primary', label, labelColorToken = '$muted',
}: ClaySpinnerProps) {
  const rotation = useSharedValue(0);
  const theme = useTheme();
  const resolvedColor = theme[colorToken.replace('$', '')]?.val ?? '#0a0a0a';
  const resolvedLabelColor = theme[labelColorToken.replace('$', '')]?.val ?? '#6a6a6a';

  useEffect(() => {
    rotation.value = withRepeat(
      withTiming(360, { duration: 800, easing: Easing.linear }),
      -1,
      false
    );
  }, [rotation]);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ rotate: `${rotation.value}deg` }],
  }));

  return (
    <YStack items="center" gap="$3">
      <Animated.View
        style={[{
          width: size, height: size, borderRadius: size / 2,
          borderWidth: 3, borderColor: resolvedColor, borderTopColor: 'transparent',
        }, animatedStyle]}
      />
      {label && (
        <Text color={resolvedLabelColor} fontSize="$body-sm">{label}</Text>
      )}
    </YStack>
  );
}

export default ClaySpinner;
