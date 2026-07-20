import React, { useEffect, useState, useCallback, useRef } from 'react';
import { FlatList, KeyboardAvoidingView, Platform } from 'react-native';
import { YStack, XStack, Text, Button, Spinner, Input } from 'tamagui';
import { useLocalSearchParams } from 'expo-router';
import { useMessages } from '@/hooks/useMessages';
import { tablesDB } from '@/lib/appwrite';
import { DATABASE_ID, TABLES } from '@/lib/constants';
import type { DealThread, Message } from '@/lib/types';

const STATUS_COLORS: Record<string, string> = {
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
  const isBrand = message.sender_type === 'brand';

  if (isSystem) {
    return (
      <YStack alignItems="center" marginVertical="$2" paddingHorizontal="$4">
        <Text fontSize={12} fontStyle="italic" color="$gray9" textAlign="center">
          {message.body}
        </Text>
        <Text fontSize={10} color="$gray10" marginTop="$1">
          {formatRelativeTime(message.timestamp)}
        </Text>
      </YStack>
    );
  }

  return (
    <YStack
      alignItems={isCreator ? 'flex-end' : 'flex-start'}
      marginVertical="$1"
      paddingHorizontal="$4"
    >
      {!isCreator && message.agent_name ? (
        <Text fontSize={11} color="$gray9" marginBottom={2} marginLeft="$1">
          {message.agent_name}
        </Text>
      ) : null}
      <YStack
        backgroundColor={isCreator ? '$blue10' : isBrand ? '$green8' : '$gray5'}
        borderRadius="$3"
        paddingHorizontal="$3"
        paddingVertical="$2"
        maxWidth="80%"
      >
        <Text
          color={isCreator ? 'white' : '$color'}
          fontSize={15}
          lineHeight={20}
        >
          {message.body}
        </Text>
      </YStack>
      <Text fontSize={10} color="$gray10" marginTop={2} marginHorizontal="$1">
        {formatRelativeTime(message.timestamp)}
      </Text>
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
      <YStack flex={1} justifyContent="center" alignItems="center" gap="$3">
        <Spinner size="large" color="$blue10" />
        <Text color="$gray10">Loading messages...</Text>
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

  // Empty state — no messages in this thread yet
  if (messages.length === 0) {
    return (
      <YStack flex={1} justifyContent="center" alignItems="center" padding="$4" gap="$3">
        <Text fontSize={16} color="$gray10" textAlign="center">
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
      <YStack flex={1} backgroundColor="$background">
        {/* Header: campaign_title, agent_assigned, status chip */}
        <XStack
          paddingHorizontal="$4"
          paddingVertical="$3"
          borderBottomWidth={1}
          borderBottomColor="$gray3"
          backgroundColor="$background"
          alignItems="center"
          justifyContent="space-between"
        >
          <YStack flex={1} gap="$1">
            <Text fontWeight="bold" fontSize={18} color="$color" numberOfLines={1}>
              {thread?.campaign_title ?? 'Thread'}
            </Text>
            {thread?.agent_assigned ? (
              <Text fontSize={13} color="$gray9">
                {thread.agent_assigned}
              </Text>
            ) : null}
          </YStack>
          {thread ? (
            <XStack
              backgroundColor={statusColor}
              borderRadius="$3"
              paddingHorizontal={10}
              paddingVertical={3}
            >
              <Text fontSize={11} fontWeight="bold" color="white" textTransform="capitalize">
                {thread.status.replace(/_/g, ' ')}
              </Text>
            </XStack>
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
          paddingHorizontal="$4"
          paddingVertical="$2"
          borderTopWidth={1}
          borderTopColor="$gray3"
          backgroundColor="$background"
          alignItems="center"
          gap="$2"
        >
          <Input
            flex={1}
            placeholder="Type a message..."
            value={inputText}
            onChangeText={setInputText}
            borderRadius="$4"
            borderWidth={1}
            borderColor="$gray4"
            fontSize={15}
            paddingHorizontal="$3"
            paddingVertical="$2"
            onSubmitEditing={handleSend}
            returnKeyType="send"
          />
          <Button
            onPress={handleSend}
            disabled={!inputText.trim() || sending}
            theme={inputText.trim() ? 'blue' : undefined}
            opacity={inputText.trim() ? 1 : 0.5}
            borderRadius="$4"
            paddingHorizontal="$4"
          >
            {sending ? (
              <Spinner size="small" />
            ) : (
              <Text fontWeight="bold" color="white">
                Send
              </Text>
            )}
          </Button>
        </XStack>
      </YStack>
    </KeyboardAvoidingView>
  );
}
