import React from 'react';
import Animated from 'react-native-reanimated';
import { YStack, Text, type ColorTokens } from 'tamagui';
import { useEntranceAnimation } from '@/hooks/useClayAnimations';

type ClayCardColor = 'pink' | 'teal' | 'lavender' | 'peach' | 'ochre' | 'cream';

interface ClayFeatureCardProps {
  children?: React.ReactNode;
  color: ClayCardColor;
  title?: string;
  description?: string;
  delay?: number;
  padding?: '$lg' | '$xl';
}

const COLOR_MAP: Record<ClayCardColor, { bg: ColorTokens; text: ColorTokens }> = {
  pink: { bg: '$brand-pink', text: '$on-dark' },
  teal: { bg: '$brand-teal', text: '$on-dark' },
  lavender: { bg: '$brand-lavender', text: '$ink' },
  peach: { bg: '$brand-peach', text: '$ink' },
  ochre: { bg: '$brand-ochre', text: '$ink' },
  cream: { bg: '$surface-card', text: '$ink' },
};

export function ClayFeatureCard({
  children, color, title, description, delay = 0, padding = '$xl',
}: ClayFeatureCardProps) {
  const { animatedStyle } = useEntranceAnimation(delay);
  const styles = COLOR_MAP[color];

  return (
    <Animated.View style={[{ flex: 1 }, animatedStyle]}>
      <YStack
        background={styles.bg}
        rounded="$xl"
        p={padding}
        gap="$3"
      >
        {title && (
          <Text color={styles.text} fontSize="$title-md" fontWeight="600" letterSpacing={-0.3}>
            {title}
          </Text>
        )}
        {description && (
          <Text color={styles.text} fontSize="$body-sm" lineHeight={22} opacity={0.9}>
            {description}
          </Text>
        )}
        {children}
      </YStack>
    </Animated.View>
  );
}

export default ClayFeatureCard;
