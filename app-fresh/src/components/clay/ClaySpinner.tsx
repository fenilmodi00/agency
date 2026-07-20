import React, { useEffect } from 'react';
import Animated, { useSharedValue, useAnimatedStyle, withRepeat, withTiming, Easing } from 'react-native-reanimated';
import { View, Text } from '@/tw';

// Clay spinner colors are known constants — no need for CSS variable resolution (Metis #7)
const CLAY_COLORS = {
  primary: '#0a0a0a',
  muted: '#6a6a6a',
} as const;

export function ClaySpinner({
  size = 40, color = 'primary', label, labelColor = 'muted',
}: {
  size?: number; color?: keyof typeof CLAY_COLORS; label?: string; labelColor?: keyof typeof CLAY_COLORS;
}) {
  const rotation = useSharedValue(0);
  const resolvedColor = CLAY_COLORS[color];
  const resolvedLabelColor = CLAY_COLORS[labelColor];

  useEffect(() => {
    rotation.value = withRepeat(withTiming(360, { duration: 800, easing: Easing.linear }), -1, false);
  }, [rotation]);

  const animatedStyle = useAnimatedStyle(() => ({ transform: [{ rotate: `${rotation.value}deg` }] }));

  return (
    <View className="items-center gap-3">
      <Animated.View
        style={[{
          width: size, height: size, borderRadius: size / 2,
          borderWidth: 3, borderColor: resolvedColor, borderTopColor: 'transparent',
        }, animatedStyle]}
      />
      {label && <Text className="text-body-sm text-muted">{label}</Text>}
    </View>
  );
}
export default ClaySpinner;
