import React, { useState, useEffect } from 'react';
import { YStack, Text, XStack, Input, ScrollView } from 'tamagui';
import { useUser, useAuth } from '@clerk/clerk-expo';
import { useRouter } from 'expo-router';
import Animated from 'react-native-reanimated';
import { useDashboard } from '@/hooks/useDashboard';
import {
  loginInstagram,
  disconnectInstagram,
  fetchMedia,
  fetchInsights,
  fetchProfile,
} from '@/lib/instagram';
import { ClayAnimatedButton } from '@/components/clay/ClayAnimatedButton';
import { ClayFeatureCard } from '@/components/clay/ClayFeatureCard';
import { ClayAnimatedCard } from '@/components/clay/ClayAnimatedCard';
import { ClaySpinner } from '@/components/clay/ClaySpinner';
import { useShakeAnimation, useEntranceAnimation } from '@/hooks/useClayAnimations';

// Shakes its children on mount — used for error messages.
function ErrorShake({ children }: { children: React.ReactNode }) {
  const { shake, animatedStyle } = useShakeAnimation();
  useEffect(() => {
    shake();
  }, [shake]);
  return <Animated.View style={animatedStyle}>{children}</Animated.View>;
}

// Fades/slides its children in on mount — used for the login form.
function Entrance({ delay = 0, children }: { delay?: number; children: React.ReactNode }) {
  const { animatedStyle } = useEntranceAnimation(delay);
  return (
    <Animated.View style={[{ width: '100%', alignItems: 'center' }, animatedStyle]}>
      {children}
    </Animated.View>
  );
}

export default function HomeScreen() {
  const { user } = useUser();
  const { getToken } = useAuth();
  const [isConnected, setIsConnected] = useState(false);
  const [username, setUsername] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [igUsername, setIgUsername] = useState('');
  const [igPassword, setIgPassword] = useState('');
  const router = useRouter();
  const { data: dashboardData, loading: dashboardLoading, error: dashboardError, refresh: refreshDashboard } = useDashboard();

  useEffect(() => {
    async function checkConnection() {
      if (!user) return;
      try {
        const profile = await fetchProfile(await getToken() ?? '');
        if (profile) {
          setIsConnected(true);
          setUsername(profile.username);
        }
      } catch (e) {
        const message = e instanceof Error ? e.message : '';
        if (message === 'session_expired') {
          setIsConnected(false);
        }
      }
    }
    checkConnection();
  }, [user]);

  async function handleLogin() {
    if (!user) return;
    setIsLoading(true);
    setError(null);
    try {
      const profile = await loginInstagram(await getToken() ?? '', user.id, igUsername, igPassword);
      setIsConnected(true);
      setUsername(profile.username);
      setIgUsername('');
      setIgPassword('');
      try { await fetchMedia(await getToken() ?? ''); } catch (e: any) {
        if (e?.message === 'session_expired') setIsConnected(false);
      }
      try { await fetchInsights(await getToken() ?? ''); } catch (e: any) {
        if (e?.message === 'session_expired') setIsConnected(false);
      }
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : 'Failed to connect';
      if (message === 'Invalid credentials') setError('Invalid Instagram credentials');
      else if (message === 'Instagram login failed') setError('Could not connect to Instagram. Check 2FA or try again.');
      else setError(message);
    } finally {
      setIsLoading(false);
    }
  }

  async function handleDisconnect() {
    setIsLoading(true);
    setError(null);
    try {
      await disconnectInstagram(await getToken() ?? '');
      setIsConnected(false);
      setUsername(null);
      setIgUsername('');
      setIgPassword('');
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : 'Failed to disconnect';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }

  // Loading state
  if (isLoading || dashboardLoading) {
    return (
      <YStack flex={1} justify="center" items="center" p="$4" gap="$2" background="$canvas">
        <ClaySpinner size={40} label="Loading..." />
      </YStack>
    );
  }

  // Error state
  if (error || dashboardError) {
    return (
      <YStack flex={1} justify="center" items="center" p="$4" gap="$4" background="$canvas">
        <ErrorShake>
          <Text color="$red10" text="center" fontSize={14}>
            {error ?? dashboardError}
          </Text>
        </ErrorShake>
        <ClayAnimatedButton variant="secondary" onPress={refreshDashboard}>
          Retry
        </ClayAnimatedButton>
      </YStack>
    );
  }

  // Not connected — login form
  if (!isConnected) {
    return (
      <YStack flex={1} justify="center" items="center" p="$4" gap="$4" background="$canvas">
        <Text fontSize="$display-sm" fontWeight="500" letterSpacing={-0.5} text="center">
          Welcome to Creator Workspace
        </Text>
        <Entrance delay={0}>
          <YStack items="center" gap="$4" width="100%" maxW={320}>
            <Text text="center" color="$muted">Connect your Instagram account to start creating.</Text>
            <Input
              placeholder="Instagram username"
              value={igUsername}
              onChangeText={setIgUsername}
              autoCapitalize="none"
              autoCorrect={false}
              width="100%"
              height={48}
              background="$canvas"
              borderColor="$hairline"
              rounded="$md"
              px="$4"
            />
            <Input
              placeholder="Instagram password"
              value={igPassword}
              onChangeText={setIgPassword}
              secureTextEntry
              autoCapitalize="none"
              autoCorrect={false}
              width="100%"
              height={48}
              background="$canvas"
              borderColor="$hairline"
              rounded="$md"
              px="$4"
            />
            <ClayAnimatedButton variant="primary" fullWidth onPress={handleLogin}>
              Connect
            </ClayAnimatedButton>
          </YStack>
        </Entrance>
        {error && (
          <Text color="$red10" text="center" fontSize={12}>
            {error}
          </Text>
        )}
      </YStack>
    );
  }

  // Empty state — connected but no dashboard data
  if (!dashboardData || (!dashboardData.deals?.length && !dashboardData.threads?.length)) {
    return (
      <YStack flex={1} justify="center" items="center" p="$4" gap="$4" background="$canvas">
        <Text fontSize="$display-sm" fontWeight="500" letterSpacing={-0.5} text="center">
          Welcome, @{username}
        </Text>
        <Text color="$muted" text="center" fontSize={14}>
          No campaign data yet — your agent will start outreach soon
        </Text>
        <ClayAnimatedButton variant="secondary" onPress={refreshDashboard}>
          Refresh
        </ClayAnimatedButton>
      </YStack>
    );
  }

  // Connected with data
  return (
    <ScrollView width="100%" background="$canvas">
      <YStack gap="$4" p="$4">
        {/* Welcome header */}
        <YStack>
          <Text fontSize="$display-sm" fontWeight="500" letterSpacing={-0.5}>
            Welcome, @{username}
          </Text>
          <Text color="$muted">Here's your campaign overview</Text>
        </YStack>

        {/* Stats cards */}
        <XStack gap="$3" flexWrap="wrap">
          <ClayFeatureCard
            color="pink"
            padding="$lg"
            title={String(dashboardData?.deals?.length ?? 0)}
            description="Active Deals"
          />
          <ClayFeatureCard
            color="teal"
            padding="$lg"
            title={String(dashboardData?.threads?.filter(t => t.unread_count > 0)?.length ?? 0)}
            description="Unread Threads"
          />
          <ClayFeatureCard
            color="ochre"
            padding="$lg"
            title={String(dashboardData?.threads?.filter(t => t.status === 'content_pending')?.length ?? 0)}
            description="Pending Content"
          />
        </XStack>

        {/* Quick-link cards */}
        <XStack gap="$3">
          <YStack flex={1}>
            <ClayAnimatedCard delay={200} onPress={() => router.push('/(tabs)/(messages)')}>
              <YStack items="center" gap="$2">
                <Text fontWeight="600">View Messages</Text>
                <Text fontSize={12} color="$muted">Check your threads</Text>
              </YStack>
            </ClayAnimatedCard>
          </YStack>
          <YStack flex={1}>
            <ClayAnimatedCard delay={200} onPress={() => router.push('/(tabs)/(profile)')}>
              <YStack items="center" gap="$2">
                <Text fontWeight="600">View Profile</Text>
                <Text fontSize={12} color="$muted">Your creator profile</Text>
              </YStack>
            </ClayAnimatedCard>
          </YStack>
        </XStack>

        {/* Recent activity */}
        <YStack gap="$2">
          <Text fontWeight="600" fontSize="$title-md">Recent Activity</Text>
          {dashboardData?.threads?.slice(0, 3).map((thread, index) => (
            <ClayAnimatedCard key={thread.$id} delay={index * 100}>
              <YStack gap="$1">
                <Text fontWeight="600">{thread.campaign_title}</Text>
                <XStack justify="space-between">
                  <Text fontSize={12} color="$muted">{thread.status}</Text>
                  <Text fontSize={12} color="$muted">
                    {thread.unread_count > 0 ? `${thread.unread_count} unread` : ''}
                  </Text>
                </XStack>
              </YStack>
            </ClayAnimatedCard>
          ))}
          {(!dashboardData?.threads || dashboardData.threads.length === 0) && (
            <Text color="$muted" fontSize={12}>No recent activity</Text>
          )}
        </YStack>

        {/* Disconnect button */}
        <YStack mt="$4">
          <ClayAnimatedButton variant="secondary" onPress={handleDisconnect}>
            Disconnect Instagram
          </ClayAnimatedButton>
        </YStack>
      </YStack>
    </ScrollView>
  );
}
