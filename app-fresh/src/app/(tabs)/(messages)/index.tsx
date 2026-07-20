import React, { useCallback, useEffect } from 'react';
import { FlatList } from 'react-native';
import Animated from 'react-native-reanimated';
import { YStack, XStack, Text } from 'tamagui';
import { useRouter } from 'expo-router';
import { useThreads } from '@/hooks/useThreads';
import type { DealThread } from '@/lib/types';
import { ClayAnimatedCard } from '@/components/clay/ClayAnimatedCard';
import { ClaySpinner } from '@/components/clay/ClaySpinner';
import { ClayAnimatedButton } from '@/components/clay/ClayAnimatedButton';
import { useShakeAnimation } from '@/hooks/useClayAnimations';

type StatusColor = '$blue10' | '$orange10' | '$green10' | '$purple10' | '$teal10' | '$gray10' | '$red10';

const STATUS_COLORS: Record<string, StatusColor> = {
  invited: '$blue10',
  negotiating: '$orange10',
  contracted: '$green10',
  content_pending: '$purple10',
  live: '$teal10',
  completed: '$gray10',
  declined: '$red10',
};

function formatTimestamp(iso: string | undefined): string {
  if (!iso) return '';
  const date = new Date(iso);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function ErrorState({ error, onRetry }: { error: string; onRetry: () => void }) {
  const { shake, animatedStyle } = useShakeAnimation();

  useEffect(() => {
    shake();
  }, [shake]);

  return (
    <YStack
      flex={1}
      justify="center"
      items="center"
      p="$4"
      gap="$4"
      background="$canvas"
    >
      <Animated.View style={animatedStyle}>
        <YStack items="center" gap="$4" maxW={320}>
          <Text color="$error" text="center" fontSize="$body-sm">
            {error}
          </Text>
          <ClayAnimatedButton variant="secondary" onPress={onRetry}>
            Retry
          </ClayAnimatedButton>
        </YStack>
      </Animated.View>
    </YStack>
  );
}

function ThreadRow({
  thread,
  index,
  onPress,
}: {
  thread: DealThread & { lastMessagePreview: string };
  index: number;
  onPress: () => void;
}) {
  const statusColor = STATUS_COLORS[thread.status] ?? '$gray10';
  const hasUnread = (thread.unread_count ?? 0) > 0;

  return (
    <YStack mx="$4" my="$1.5">
      <ClayAnimatedCard onPress={onPress} delay={index * 80}>
        <YStack gap="$2">
          {/* Top row: title + unread badge + timestamp */}
          <XStack justify="space-between" items="center">
            <XStack flex={1} items="center" gap="$2">
              <Text
                fontSize="$title-sm"
                fontWeight="600"
                color="$ink"
                numberOfLines={1}
                flex={1}
              >
                {thread.campaign_title}
              </Text>
              {hasUnread && (
                <Text
                  fontSize="$caption"
                  color="$on-primary"
                  background="$error"
                  rounded="$pill"
                  minW={22}
                  text="center"
                  px={6}
                >
                  {thread.unread_count > 99 ? '99+' : thread.unread_count}
                </Text>
              )}
            </XStack>
            <Text fontSize="$caption" color="$muted-soft" ml="$2">
              {formatTimestamp(thread.last_message_at)}
            </Text>
          </XStack>

          {/* Preview text */}
          <Text fontSize="$body-sm" color="$muted" numberOfLines={2}>
            {thread.lastMessagePreview || 'No messages yet'}
          </Text>

          {/* Bottom row: status chip + agent */}
          <XStack justify="space-between" items="center" mt="$1">
            <Text
              fontSize="$caption-uppercase"
              fontWeight="600"
              color="$on-primary"
              background={statusColor}
              rounded="$sm"
              px={8}
              py={2}
            >
              {thread.status.replace(/_/g, ' ')}
            </Text>
            {thread.agent_assigned && (
              <Text fontSize="$caption" color="$muted-soft">
                {thread.agent_assigned}
              </Text>
            )}
          </XStack>
        </YStack>
      </ClayAnimatedCard>
    </YStack>
  );
}

export default function MessagesScreen() {
  const { threads, loading, error, refresh } = useThreads();
  const router = useRouter();

  const handlePress = useCallback(
    (thread: DealThread) => {
      router.push(`/(tabs)/(messages)/${thread.$id}`);
    },
    [router]
  );

  const renderItem = useCallback(
    ({ item, index }: { item: DealThread & { lastMessagePreview: string }; index: number }) => (
      <ThreadRow thread={item} index={index} onPress={() => handlePress(item)} />
    ),
    [handlePress]
  );

  const keyExtractor = useCallback(
    (item: DealThread & { lastMessagePreview: string }) => item.$id ?? item.thread_id,
    []
  );

  // Loading state
  if (loading) {
    return (
      <YStack
        flex={1}
        justify="center"
        items="center"
        background="$canvas"
      >
        <ClaySpinner size={40} label="Loading threads..." />
      </YStack>
    );
  }

  // Error state
  if (error) {
    return <ErrorState error={error} onRetry={refresh} />;
  }

  // Empty state
  if (threads.length === 0) {
    return (
      <YStack
        flex={1}
        justify="center"
        items="center"
        p="$4"
        gap="$3"
        background="$canvas"
      >
        <Text fontSize="$body-sm" color="$muted" text="center">
          No deal threads yet — your agent will start outreach soon
        </Text>
      </YStack>
    );
  }

  // Threads list
  return (
    <YStack flex={1} background="$canvas">
      <FlatList
        data={threads}
        renderItem={renderItem}
        keyExtractor={keyExtractor}
        contentContainerStyle={{ paddingVertical: 8 }}
        showsVerticalScrollIndicator={false}
      />
    </YStack>
  );
}
