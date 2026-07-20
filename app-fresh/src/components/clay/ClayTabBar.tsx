import React, { useEffect } from 'react';
import { Pressable, Dimensions } from 'react-native';
import Animated, { useSharedValue, useAnimatedStyle, withSpring } from 'react-native-reanimated';
import { YStack, XStack, Text } from 'tamagui';
import { Ionicons } from '@expo/vector-icons';
import type { BottomTabBarProps } from '@react-navigation/bottom-tabs';

const TAB_COUNT = 3;
const TAB_WIDTH = Dimensions.get('window').width / TAB_COUNT;

const TABS = [
  { name: '(home)', label: 'Home', icon: 'home' as const },
  { name: '(messages)', label: 'Messages', icon: 'chatbubbles' as const },
  { name: '(profile)', label: 'Profile', icon: 'person' as const },
];

export function ClayTabBar({ state, navigation, insets }: BottomTabBarProps) {
  const translateX = useSharedValue(state.index * TAB_WIDTH);

  useEffect(() => {
    translateX.value = withSpring(state.index * TAB_WIDTH, {
      damping: 20,
      stiffness: 200,
    });
  }, [state.index, translateX]);

  const indicatorStyle = useAnimatedStyle(() => ({
    transform: [{ translateX: translateX.value }],
  }));

  return (
    <YStack background="$canvas" borderTopWidth={1} borderTopColor="$hairline" pb={insets.bottom}>
      <XStack height={64}>
        {TABS.map((tab, index) => {
          const isFocused = state.index === index;
          return (
            <Pressable
              key={tab.name}
              style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}
              onPress={() => {
                const event = navigation.emit({
                  type: 'tabPress',
                  target: state.routes[index].key,
                  canPreventDefault: true,
                });
                if (!isFocused && !event.defaultPrevented) {
                  navigation.navigate(tab.name);
                }
              }}
            >
              <Ionicons name={tab.icon} size={24} color={isFocused ? '#0a0a0a' : '#6a6a6a'} />
              <Text fontSize="$caption" fontWeight={isFocused ? '600' : '500'} color={isFocused ? '$ink' : '$muted'} mt="$xs">
                {tab.label}
              </Text>
            </Pressable>
          );
        })}
        <Animated.View
          style={[{
            position: 'absolute', bottom: 0, width: TAB_WIDTH, height: 3,
            backgroundColor: '#0a0a0a', borderTopLeftRadius: 3, borderTopRightRadius: 3,
          }, indicatorStyle]}
        />
      </XStack>
    </YStack>
  );
}

export default ClayTabBar;
