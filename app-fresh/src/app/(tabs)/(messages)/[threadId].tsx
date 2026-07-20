import React, { useEffect, useState, useCallback, useRef } from 'react';
import { FlatList, KeyboardAvoidingView, Platform } from 'react-native';
import { YStack, XStack, Text, Input } from 'tamagui';
import Animated, { SlideInUp } from 'react-native-reanimated';
import { useLocalSearchParams } from 'expo-router';
import { ClayAnimatedButton } from '@/components/clay/ClayAnimatedButton';
import { ClaySpinner } from '@/components/clay/ClaySpinner';
import { useShakeAnimation } from '@/hooks/useClayAnimations';
import { useMessages } from '@/hooks/useMessages';
import { tablesDB } from '@/lib/appwrite';
import { DATABASE_ID, TABLES } from '@/lib/constants';
import type { DealThread, Message } from '@/lib/types';

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

function formatRelativeTime(iso: string): string {
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

function MessageBubble({ message }: { message: Message }) {
  const isCreator = message.sender_type === 'creator';
  const isSystem = message.sender_type === 'system';

  if (isSystem) {
    return (
      <YStack items="center" my="$2" px="$4">
        <Text fontSize="$caption" fontStyle="italic" color="$muted" text="center">
          {message.body}
        </Text>
        <Text fontSize="$caption" color="$muted-soft" mt="$1">
          {formatRelativeTime(message.timestamp)}
        </Text>
      </YStack>
    );
  }

  return (
    <Animated.View entering={SlideInUp}>
      <YStack
        items={isCreator ? 'flex-end' : 'flex-start'}
        my="$1"
        px="$4"
      >
        {!isCreator && message.agent_name ? (
          <Text fontSize="$caption" color="$muted" mb={2} ml="$1">
            {message.agent_name}
          </Text>
        ) : null}
        <YStack
          background={isCreator ? '$brand-teal' : '$surface-card'}
          rounded="$lg"
          px="$3"
          py="$2"
          maxW="80%"
        >
          <Text
            color={isCreator ? '$on-dark' : '$ink'}
            fontSize="$body-md"
            lineHeight={22}
          >
            {message.body}
          </Text>
        </YStack>
        <Text fontSize="$caption" color="$muted-soft" mt={2} mx="$1">
          {formatRelativeTime(message.timestamp)}
        </Text>
      </YStack>
    </Animated.View>
  );
}

function ErrorState({ error, onRetry }: { error: string; onRetry: () => void }) {
  const { shake, animatedStyle } = useShakeAnimation();

  useEffect(() => {
    shake();
  }, [shake]);

  return (
    <YStack flex={1} justify="center" items="center" p="$4" background="$canvas">
      <Animated.View style={animatedStyle}>
        <YStack items="center" gap="$4" p="$4">
          <Text color="$red10" text="center" fontSize="$body-sm">
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

export default function ThreadDetail() {
  const { threadId } = useLocalSearchParams<{ threadId: string }>();
  const { messages, loading, error, sendMessage, markAsRead, refresh } = useMessages(threadId ?? '');
  const [thread, setThread] = useState<DealThread | null>(null);
  const [inputText, setInputText] = useState('');
  const [sending, setSending] = useState(false);
  const flatListRef = useRef<FlatList>(null);

  // Fetch thread details (campaign_title, agent_assigned, status)
  useEffect(() => {
    if (!threadId) return;
    (async () => {
      try {
        const result = await tablesDB.getRow({
          databaseId: DATABASE_ID,
          tableId: TABLES.DEAL_THREADS,
          rowId: threadId,
        });
        setThread(result as unknown as DealThread);
      } catch {
        // Thread details are not critical for rendering messages
      }
    })();
  }, [threadId]);

  // Mark all messages as read on mount
  useEffect(() => {
    if (threadId) {
      markAsRead();
    }
  }, [threadId, markAsRead]);

  const handleSend = useCallback(async () => {
    const text = inputText.trim();
    if (!text || sending) return;
    setSending(true);
    try {
      await sendMessage(text);
      setInputText('');
    } catch {
      // Error is surfaced by the hook
    } finally {
      setSending(false);
    }
  }, [inputText, sending, sendMessage]);

  const renderItem = useCallback(
    ({ item }: { item: Message }) => <MessageBubble message={item} />,
    [],
  );

  const keyExtractor = useCallback(
    (item: Message) => item.$id ?? item.message_id,
    [],
  );

  // Loading state
  if (loading) {
    return (
      <YStack flex={1} justify="center" items="center" background="$canvas">
        <ClaySpinner size={40} label="Loading messages..." />
      </YStack>
    );
  }

  // Error state — shake animation + retry
  if (error) {
    return <ErrorState error={error} onRetry={refresh} />;
  }

  // Empty state — no messages in this thread yet
  if (messages.length === 0) {
    return (
      <YStack flex={1} justify="center" items="center" p="$4" background="$canvas">
        <Text fontSize="$body-md" color="$muted" text="center">
          No messages yet — start the conversation
        </Text>
      </YStack>
    );
  }

  const statusColor = thread ? (STATUS_COLORS[thread.status] ?? '$gray10') : '$gray10';

  return (
    <KeyboardAvoidingView
      style={{ flex: 1 }}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
    >
      <YStack flex={1} background="$canvas">
        {/* Header: campaign_title, agent_assigned, status chip */}
        <XStack
          px="$4"
          py="$3"
          background="$canvas"
          borderBottomWidth={1}
          borderBottomColor="$hairline"
          items="center"
          justify="space-between"
        >
          <YStack flex={1} gap="$1">
            <Text fontSize="$title-md" fontWeight="600" color="$ink" numberOfLines={1}>
              {thread?.campaign_title ?? 'Thread'}
            </Text>
            {thread?.agent_assigned ? (
              <Text fontSize="$body-sm" color="$muted">
                {thread.agent_assigned}
              </Text>
            ) : null}
          </YStack>
          {thread ? (
            <Text
              fontSize="$caption-uppercase"
              fontWeight="600"
              color="$on-primary"
              background={statusColor}
              rounded="$sm"
              px={10}
              py={3}
              textTransform="capitalize"
            >
              {thread.status.replace(/_/g, ' ')}
            </Text>
          ) : null}
        </XStack>

        {/* Message list — inverted for chat-style scrolling */}
        <YStack flex={1}>
          <FlatList
            ref={flatListRef}
            data={messages}
            renderItem={renderItem}
            keyExtractor={keyExtractor}
            inverted={true}
            contentContainerStyle={{ paddingVertical: 12 }}
            showsVerticalScrollIndicator={false}
          />
        </YStack>

        {/* Input bar */}
        <XStack
          px="$4"
          py="$2"
          background="$canvas"
          borderTopWidth={1}
          borderTopColor="$hairline"
          items="center"
          gap="$2"
        >
          <Input
            flex={1}
            placeholder="Type a message..."
            value={inputText}
            onChangeText={setInputText}
            background="$canvas"
            borderWidth={1}
            borderColor="$hairline"
            rounded="$md"
            height={44}
            fontSize="$body-md"
            px="$3"
            onSubmitEditing={handleSend}
            returnKeyType="send"
          />
          <ClayAnimatedButton
            variant="primary"
            onPress={handleSend}
            loading={sending}
            disabled={!inputText.trim() || sending}
          >
            Send
          </ClayAnimatedButton>
        </XStack>
      </YStack>
    </KeyboardAvoidingView>
  );
}
