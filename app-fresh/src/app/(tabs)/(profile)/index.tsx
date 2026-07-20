import React, { useEffect } from 'react';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
} from 'react-native-reanimated';
import {
  YStack,
  XStack,
  Text,
  Image,
  H3,
  Avatar,
  ScrollView,
} from 'tamagui';
import { useUser, useAuth, useClerk } from '@clerk/clerk-expo';
import { useCreatorProfile } from '@/hooks/useCreatorProfile';
import { useDashboard } from '@/hooks/useDashboard';
import { disconnectInstagram } from '@/lib/instagram';
import { ClaySpinner } from '@/components/clay/ClaySpinner';
import { ClayAnimatedCard } from '@/components/clay/ClayAnimatedCard';
import { ClayAnimatedButton } from '@/components/clay/ClayAnimatedButton';
import { ClayFeatureCard } from '@/components/clay/ClayFeatureCard';
import { useShakeAnimation } from '@/hooks/useClayAnimations';

function formatCount(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

function statusColor(status: string): '$blue10' | '$orange10' | '$purple10' | '$yellow10' | '$green10' | '$gray10' | '$red10' {
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
          <Text color="$error" text="center" fontSize="$body-md">
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

  // Avatar scale-in entrance
  const avatarScale = useSharedValue(0);
  useEffect(() => {
    avatarScale.value = withSpring(1, { damping: 12, stiffness: 140 });
  }, [avatarScale]);
  const avatarAnimatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: avatarScale.value }],
  }));

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
      <YStack
        flex={1}
        justify="center"
        items="center"
        p="$4"
        background="$canvas"
      >
        <ClaySpinner size={40} label="Loading profile..." />
      </YStack>
    );
  }

  // Error state
  if (error) {
    return <ErrorState error={error} onRetry={refresh} />;
  }

  // Empty state — no creator connected
  if (!creator) {
    return (
      <YStack
        flex={1}
        justify="center"
        items="center"
        p="$4"
        gap="$4"
        background="$canvas"
      >
        <Text text="center" fontSize="$body-md" color="$body">
          Connect your Instagram to see your profile
        </Text>
        <ClayAnimatedButton variant="secondary" onPress={refresh}>
          Refresh
        </ClayAnimatedButton>
      </YStack>
    );
  }

  return (
    <ScrollView flex={1} background="$canvas">
      <YStack p="$4" gap="$4">
        {/* Creator Card */}
        <ClayAnimatedCard delay={0}>
          <XStack gap="$4" items="center">
            <Animated.View style={avatarAnimatedStyle}>
              <Avatar circular size="$8">
                <Avatar.Image src={creator.profile_pic_url} />
                <Avatar.Fallback background="$surface-card" />
              </Avatar>
            </Animated.View>
            <YStack flex={1} gap="$1">
              <Text fontWeight="600" fontSize="$title-md" color="$ink" letterSpacing={-0.3}>
                {creator.full_name}
              </Text>
              <Text color="$muted" fontSize="$body-sm">
                @{creator.ig_username}
              </Text>
              <XStack gap="$2" flexWrap="wrap" mt="$1">
                <Text
                  fontSize="$caption"
                  color="$body"
                  background="$surface-card"
                  px="$2"
                  py="$1"
                  rounded="$pill"
                >
                  {formatCount(creator.follower_count)} followers
                </Text>
                <Text
                  fontSize="$caption"
                  color="$body"
                  background="$surface-card"
                  px="$2"
                  py="$1"
                  rounded="$pill"
                >
                  {formatCount(creator.following_count)} following
                </Text>
                <Text
                  fontSize="$caption"
                  color="$body"
                  background="$surface-card"
                  px="$2"
                  py="$1"
                  rounded="$pill"
                >
                  {formatCount(creator.media_count)} posts
                </Text>
              </XStack>
            </YStack>
          </XStack>

          {/* Badges */}
          <XStack gap="$2" mt="$3" flexWrap="wrap">
            <Text
              fontSize="$caption"
              background="$brand-mint"
              color="$ink"
              px="$3"
              py="$1"
              rounded="$pill"
            >
              {creator.engagement_rate.toFixed(1)}% engagement
            </Text>
            <Text
              fontSize="$caption"
              background="$brand-lavender"
              color="$ink"
              px="$3"
              py="$1"
              rounded="$pill"
            >
              {creator.creator_tier.replace(/_/g, ' ')}
            </Text>
            <Text
              fontSize="$caption"
              background="$brand-peach"
              color="$ink"
              px="$3"
              py="$1"
              rounded="$pill"
            >
              {creator.niche}
            </Text>
          </XStack>
        </ClayAnimatedCard>

        {/* Recent Reels */}
        <YStack gap="$2">
          <H3 color="$ink" fontSize="$title-md" fontWeight="600" letterSpacing={-0.3}>
            Recent Reels
          </H3>
          {recentReels.length > 0 ? (
            <ScrollView horizontal showsHorizontalScrollIndicator={false}>
              <XStack gap="$3" pb="$2">
                {recentReels.map((reel, index) => (
                  <ClayAnimatedCard
                    key={reel.$id ?? index}
                    delay={index * 100}
                    padding="$0"
                  >
                    <YStack width={160}>
                      <Image
                        source={{ uri: reel.display_url ?? '' }}
                        width={160}
                        height={200}
                        rounded="$sm"
                      />
                      <YStack p="$2">
                        <Text fontSize="$caption" color="$muted">
                          {formatCount(reel.video_view_count)} views
                        </Text>
                      </YStack>
                    </YStack>
                  </ClayAnimatedCard>
                ))}
              </XStack>
            </ScrollView>
          ) : (
            <Text color="$muted" fontSize="$body-sm">
              No recent reels
            </Text>
          )}
        </YStack>

        {/* Insights Summary */}
        <YStack gap="$2">
          {insights?.data ? (
            <ClayFeatureCard color="cream" title="Insights" delay={200}>
              <YStack gap="$2">
                {insights.data.map((metric, index) => (
                  <XStack key={index} justify="space-between">
                    <Text fontSize="$body-sm" color="$body" textTransform="capitalize">
                      {metric.name.replace(/_/g, ' ')}
                    </Text>
                    <Text fontWeight="600" fontSize="$body-sm" color="$ink">
                      {metric.values[0]?.value ?? '—'}
                    </Text>
                  </XStack>
                ))}
              </YStack>
            </ClayFeatureCard>
          ) : (
            <YStack gap="$2">
              <H3 color="$ink" fontSize="$title-md" fontWeight="600" letterSpacing={-0.3}>
                Insights
              </H3>
              <Text color="$muted" fontSize="$body-sm">
                Insights available for business accounts only
              </Text>
            </YStack>
          )}
        </YStack>

        {/* Active Deals */}
        <YStack gap="$2">
          <H3 color="$ink" fontSize="$title-md" fontWeight="600" letterSpacing={-0.3}>
            Active Deals
          </H3>
          {dealThreads.length > 0 ? (
            <YStack gap="$2">
              {dealThreads.map((thread, index) => (
                <ClayAnimatedCard
                  key={thread.$id ?? thread.thread_id}
                  delay={index * 100}
                  padding="$md"
                >
                  <XStack justify="space-between" items="center">
                    <YStack flex={1} gap="$1">
                      <Text fontWeight="600" fontSize="$body-sm" color="$ink">
                        {thread.campaign_title}
                      </Text>
                      <Text fontSize="$caption" color="$muted">
                        {thread.agent_assigned}
                      </Text>
                    </YStack>
                    <XStack gap="$2" items="center">
                      <Text
                        fontSize="$caption"
                        background={statusColor(thread.status)}
                        color="$on-primary"
                        px="$2"
                        py="$1"
                        rounded="$pill"
                      >
                        {thread.status.replace(/_/g, ' ')}
                      </Text>
                      {thread.unread_count > 0 && (
                        <Text
                          fontSize="$caption"
                          background="$error"
                          color="$on-primary"
                          width={22}
                          height={22}
                          text="center"
                          lineHeight={22}
                          rounded={11}
                        >
                          {thread.unread_count}
                        </Text>
                      )}
                    </XStack>
                  </XStack>
                </ClayAnimatedCard>
              ))}
            </YStack>
          ) : (
            <Text color="$muted" fontSize="$body-sm">
              No active deals
            </Text>
          )}
        </YStack>

        {/* Action Buttons */}
        <YStack gap="$3" mt="$4">
          <ClayAnimatedButton variant="secondary" onPress={handleDisconnect} fullWidth>
            Disconnect Instagram
          </ClayAnimatedButton>
          <ClayAnimatedButton variant="primary" onPress={() => signOut()} fullWidth>
            Sign Out
          </ClayAnimatedButton>
        </YStack>
      </YStack>
    </ScrollView>
  );
}
