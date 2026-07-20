import React from 'react';
import {
  YStack,
  XStack,
  Text,
  Button,
  Image,
  Card,
  Spinner,
  H2,
  H3,
  Avatar,
  ScrollView,
} from 'tamagui';
import { useUser, useAuth, useClerk } from '@clerk/clerk-expo';
import { useCreatorProfile } from '@/hooks/useCreatorProfile';
import { useDashboard } from '@/hooks/useDashboard';
import { disconnectInstagram } from '@/lib/instagram';

function formatCount(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

function statusColor(status: string): string {
  switch (status) {
    case 'invited':
      return '$blue10';
    case 'negotiating':
      return '$orange10';
    case 'contracted':
      return '$purple10';
    case 'content_pending':
      return '$yellow10';
    case 'live':
      return '$green10';
    case 'completed':
      return '$gray10';
    case 'declined':
      return '$red10';
    default:
      return '$gray10';
  }
}

export default function ProfileScreen() {
  const { user } = useUser();
  const { getToken } = useAuth();
  const { signOut } = useClerk();
  const {
    creator,
    dealThreads,
    recentReels,
    insights,
    isLoading,
    error,
    refresh,
  } = useCreatorProfile();
  const { data: dashboardData, loading: dashboardLoading } = useDashboard();

  async function handleDisconnect() {
    try {
      await disconnectInstagram(await getToken() ?? '');
      refresh();
    } catch {
      // Silently handle — user can retry
    }
  }

  // Loading state
  if (isLoading || dashboardLoading) {
    return (
      <YStack flex={1} justifyContent="center" alignItems="center" padding="$4">
        <Spinner size="large" color="$blue10" />
        <Text marginTop="$2">Loading profile...</Text>
      </YStack>
    );
  }

  // Error state
  if (error) {
    return (
      <YStack flex={1} justifyContent="center" alignItems="center" padding="$4" gap="$4">
        <Text color="$red10" textAlign="center">
          {error}
        </Text>
        <Button onPress={refresh} theme="blue">
          Retry
        </Button>
      </YStack>
    );
  }

  // Empty state — no creator connected
  if (!creator) {
    return (
      <YStack flex={1} justifyContent="center" alignItems="center" padding="$4" gap="$4">
        <Text textAlign="center" fontSize={16}>
          Connect your Instagram to see your profile
        </Text>
        <Button onPress={refresh} theme="blue">
          Refresh
        </Button>
      </YStack>
    );
  }

  return (
    <ScrollView flex={1} backgroundColor="$background">
      <YStack padding="$4" gap="$4">
        {/* Creator Card */}
        <Card padding="$4" borderRadius="$4" elevation="$2" borderWidth={1} borderColor="$borderColor">
          <XStack gap="$4" alignItems="center">
            <Avatar circular size="$8">
              <Avatar.Image src={creator.profile_pic_url} />
              <Avatar.Fallback backgroundColor="$gray5" />
            </Avatar>
            <YStack flex={1} gap="$1">
              <Text fontWeight="bold" fontSize={18}>
                {creator.full_name}
              </Text>
              <Text color="$gray10" fontSize={14}>
                @{creator.ig_username}
              </Text>
              <XStack gap="$2" flexWrap="wrap" marginTop="$1">
                <Text
                  fontSize={12}
                  backgroundColor="$blue2"
                  paddingHorizontal="$2"
                  paddingVertical="$1"
                  borderRadius="$2"
                >
                  {formatCount(creator.follower_count)} followers
                </Text>
                <Text
                  fontSize={12}
                  backgroundColor="$blue2"
                  paddingHorizontal="$2"
                  paddingVertical="$1"
                  borderRadius="$2"
                >
                  {formatCount(creator.following_count)} following
                </Text>
                <Text
                  fontSize={12}
                  backgroundColor="$blue2"
                  paddingHorizontal="$2"
                  paddingVertical="$1"
                  borderRadius="$2"
                >
                  {formatCount(creator.media_count)} posts
                </Text>
              </XStack>
            </YStack>
          </XStack>

          {/* Badges */}
          <XStack gap="$2" marginTop="$3" flexWrap="wrap">
            <Text
              fontSize={12}
              backgroundColor="$green2"
              color="$green10"
              paddingHorizontal="$3"
              paddingVertical="$1"
              borderRadius="$10"
            >
              {creator.engagement_rate.toFixed(1)}% engagement
            </Text>
            <Text
              fontSize={12}
              backgroundColor="$purple2"
              color="$purple10"
              paddingHorizontal="$3"
              paddingVertical="$1"
              borderRadius="$10"
            >
              {creator.creator_tier.replace(/_/g, ' ')}
            </Text>
            <Text
              fontSize={12}
              backgroundColor="$orange2"
              color="$orange10"
              paddingHorizontal="$3"
              paddingVertical="$1"
              borderRadius="$10"
            >
              {creator.niche}
            </Text>
          </XStack>
        </Card>

        {/* Recent Reels */}
        <YStack gap="$2">
          <H3>Recent Reels</H3>
          {recentReels.length > 0 ? (
            <ScrollView horizontal showsHorizontalScrollIndicator={false}>
              <XStack gap="$3" paddingBottom="$2">
                {recentReels.map((reel, index) => (
                  <Card key={reel.$id ?? index} width={160} borderWidth={1} borderColor="$borderColor" elevation="$2">
                    <Image
                      source={{ uri: reel.display_url ?? '' }}
                      width={160}
                      height={200}
                      borderRadius="$2"
                    />
                    <YStack padding="$2">
                      <Text fontSize={12} color="$gray10">
                        {formatCount(reel.video_view_count)} views
                      </Text>
                    </YStack>
                  </Card>
                ))}
              </XStack>
            </ScrollView>
          ) : (
            <Text color="$gray10" fontSize={14}>
              No recent reels
            </Text>
          )}
        </YStack>

        {/* Insights Summary */}
        <YStack gap="$2">
          <H3>Insights</H3>
          {insights?.data ? (
            <Card borderWidth={1} borderColor="$borderColor" padding="$3" elevation="$2">
              <YStack gap="$2">
                {insights.data.map((metric, index) => (
                  <XStack key={index} justifyContent="space-between">
                    <Text fontSize={14} textTransform="capitalize">
                      {metric.name.replace(/_/g, ' ')}
                    </Text>
                    <Text fontWeight="bold" fontSize={14}>
                      {metric.values[0]?.value ?? '—'}
                    </Text>
                  </XStack>
                ))}
              </YStack>
            </Card>
          ) : (
            <Text color="$gray10" fontSize={14}>
              Insights available for business accounts only
            </Text>
          )}
        </YStack>

        {/* Active Deals */}
        <YStack gap="$2">
          <H3>Active Deals</H3>
          {dealThreads.length > 0 ? (
            <YStack gap="$2">
              {dealThreads.map((thread) => (
                <Card
                  key={thread.$id ?? thread.thread_id}
                  borderWidth={1} borderColor="$borderColor"
                  padding="$3"
                  elevation="$2"
                >
                  <XStack justifyContent="space-between" alignItems="center">
                    <YStack flex={1} gap="$1">
                      <Text fontWeight="bold" fontSize={14}>
                        {thread.campaign_title}
                      </Text>
                      <Text fontSize={12} color="$gray10">
                        {thread.agent_assigned}
                      </Text>
                    </YStack>
                    <XStack gap="$2" alignItems="center">
                      <Text
                        fontSize={12}
                        backgroundColor={statusColor(thread.status)}
                        color="white"
                        paddingHorizontal="$2"
                        paddingVertical="$1"
                        borderRadius="$10"
                      >
                        {thread.status.replace(/_/g, ' ')}
                      </Text>
                      {thread.unread_count > 0 && (
                        <Text
                          fontSize={12}
                          backgroundColor="$red10"
                          color="white"
                          width={22}
                          height={22}
                          textAlign="center"
                          lineHeight={22}
                          borderRadius={11}
                        >
                          {thread.unread_count}
                        </Text>
                      )}
                    </XStack>
                  </XStack>
                </Card>
              ))}
            </YStack>
          ) : (
            <Text color="$gray10" fontSize={14}>
              No active deals
            </Text>
          )}
        </YStack>

        {/* Action Buttons */}
        <YStack gap="$3" marginTop="$4">
          <Button onPress={handleDisconnect} theme="red">
            Disconnect Instagram
          </Button>
          <Button onPress={() => signOut()} theme="gray">
            Sign Out
          </Button>
        </YStack>
      </YStack>
    </ScrollView>
  );
}
