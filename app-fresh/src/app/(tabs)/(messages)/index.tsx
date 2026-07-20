import React, { useCallback } from 'react';
import { FlatList, TouchableOpacity } from 'react-native';
import { YStack, XStack, Text, Button, Spinner, H2, Card } from 'tamagui';
import { useRouter } from 'expo-router';
import { useThreads } from '@/hooks/useThreads';
import type { DealThread } from '@/lib/types';

const STATUS_COLORS: Record<string, string> = {
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

function ThreadRow({
  thread,
  onPress,
}: {
  thread: DealThread & { lastMessagePreview: string };
  onPress: () => void;
}) {
  const statusColor = STATUS_COLORS[thread.status] ?? '$gray10';
  const hasUnread = (thread.unread_count ?? 0) > 0;

  return (
    <TouchableOpacity onPress={onPress} activeOpacity={0.7}>
      <Card
        marginHorizontal="$4"
        marginVertical="$1.5"
        padding="$4"
        borderRadius="$4"
        borderWidth={1}
        borderColor={hasUnread ? '$blue8' : '$gray3'}
      >
        <YStack gap="$2">
          {/* Top row: title + unread badge */}
          <XStack justifyContent="space-between" alignItems="center">
            <XStack flex={1} alignItems="center" gap="$2">
              <Text
                fontWeight="bold"
                fontSize={16}
                color="$color"
                numberOfLines={1}
                flex={1}
              >
                {thread.campaign_title}
              </Text>
              {hasUnread && (
                <XStack
                  backgroundColor="$red9"
                  borderRadius={12}
                  minWidth={22}
                  height={22}
                  justifyContent="center"
                  alignItems="center"
                  paddingHorizontal={6}
                >
                  <Text fontSize={11} fontWeight="bold" color="white">
                    {thread.unread_count > 99 ? '99+' : thread.unread_count}
                  </Text>
                </XStack>
              )}
            </XStack>
            <Text fontSize={12} color="$gray9" marginLeft="$2">
              {formatTimestamp(thread.last_message_at)}
            </Text>
          </XStack>

          {/* Preview text */}
          <Text fontSize={14} color="$gray10" numberOfLines={2}>
            {thread.lastMessagePreview || 'No messages yet'}
          </Text>

          {/* Bottom row: status chip + agent */}
          <XStack justifyContent="space-between" alignItems="center" marginTop="$1">
            <XStack
              backgroundColor={statusColor}
              borderRadius="$3"
              paddingHorizontal={8}
              paddingVertical={2}
            >
              <Text fontSize={11} fontWeight="bold" color="white" textTransform="capitalize">
                {thread.status.replace(/_/g, ' ')}
              </Text>
            </XStack>
            {thread.agent_assigned && (
              <Text fontSize={12} color="$gray9">
                {thread.agent_assigned}
              </Text>
            )}
          </XStack>
        </YStack>
      </Card>
    </TouchableOpacity>
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
    ({ item }: { item: DealThread & { lastMessagePreview: string } }) => (
      <ThreadRow thread={item} onPress={() => handlePress(item)} />
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
      <YStack flex={1} justifyContent="center" alignItems="center" gap="$3">
        <Spinner size="large" color="$blue10" />
        <Text color="$gray10">Loading threads...</Text>
      </YStack>
    );
  }

  // Error state
  if (error) {
    return (
      <YStack flex={1} justifyContent="center" alignItems="center" padding="$4" gap="$4">
        <Text color="$red10" textAlign="center" fontSize={14}>
          {error}
        </Text>
        <Button onPress={refresh} theme="blue">
          Retry
        </Button>
      </YStack>
    );
  }

  // Empty state
  if (threads.length === 0) {
    return (
      <YStack flex={1} justifyContent="center" alignItems="center" padding="$4" gap="$3">
        <Text fontSize={16} color="$gray10" textAlign="center">
          No deal threads yet — your agent will start outreach soon
        </Text>
      </YStack>
    );
  }

  // Threads list
  return (
    <YStack flex={1} backgroundColor="$background">
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
