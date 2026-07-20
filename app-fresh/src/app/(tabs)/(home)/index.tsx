import React, { useState, useEffect } from 'react';
import { YStack, Text, Button, Spinner, H2, XStack, Input, Card, H3, ScrollView } from 'tamagui';
import { useUser, useAuth } from '@clerk/clerk-expo';
import { useRouter } from 'expo-router';
import { useDashboard } from '@/hooks/useDashboard';
import {
  loginInstagram,
  disconnectInstagram,
  fetchMedia,
  fetchInsights,
  fetchProfile,
} from '@/lib/instagram';

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
      <YStack flex={1} justifyContent="center" alignItems="center" padding="$4" gap="$2">
        <Spinner size="large" color="$blue10" />
        <Text>Loading...</Text>
      </YStack>
    );
  }

  // Error state
  if (error || dashboardError) {
    return (
      <YStack flex={1} justifyContent="center" alignItems="center" padding="$4" gap="$4">
        <Text color="$red10" textAlign="center" fontSize={14}>
          {error ?? dashboardError}
        </Text>
        <Button onPress={refreshDashboard} theme="blue">
          Retry
        </Button>
      </YStack>
    );
  }

  // Not connected — login form
  if (!isConnected) {
    return (
      <YStack flex={1} justifyContent="center" alignItems="center" padding="$4" gap="$4">
        <H2 textAlign="center">Welcome to Creator Workspace</H2>
        <YStack alignItems="center" gap="$4" width="100%" maxWidth={320}>
          <Text textAlign="center">Connect your Instagram account to start creating.</Text>
          <Input
            placeholder="Instagram username"
            value={igUsername}
            onChangeText={setIgUsername}
            autoCapitalize="none"
            autoCorrect={false}
            width="100%"
          />
          <Input
            placeholder="Instagram password"
            value={igPassword}
            onChangeText={setIgPassword}
            secureTextEntry
            autoCapitalize="none"
            autoCorrect={false}
            width="100%"
          />
          <Button onPress={handleLogin} theme="blue" width="100%">
            Connect
          </Button>
        </YStack>
        {error && (
          <Text color="$red10" textAlign="center" fontSize={12}>
            {error}
          </Text>
        )}
      </YStack>
    );
  }

  // Empty state — connected but no dashboard data
  if (!dashboardData || (!dashboardData.deals?.length && !dashboardData.threads?.length)) {
    return (
      <YStack flex={1} justifyContent="center" alignItems="center" padding="$4" gap="$4">
        <H2 textAlign="center">Welcome, @{username}</H2>
        <Text color="$gray10" textAlign="center" fontSize={14}>
          No campaign data yet — your agent will start outreach soon
        </Text>
        <Button onPress={refreshDashboard} theme="blue">
          Refresh
        </Button>
      </YStack>
    );
  }

  // Connected with data
  return (
    <ScrollView width="100%">
      <YStack gap="$4" padding="$4">
        {/* Welcome header */}
        <YStack>
          <H2>Welcome, @{username}</H2>
          <Text color="$gray10">Here's your campaign overview</Text>
        </YStack>

        {/* Stats cards */}
        <XStack gap="$3" flexWrap="wrap">
          <Card flex={1} minWidth={100} padding="$3" backgroundColor="$blue2">
            <YStack alignItems="center">
              <H3>{dashboardData?.deals?.length ?? 0}</H3>
              <Text fontSize={12}>Active Deals</Text>
            </YStack>
          </Card>
          <Card flex={1} minWidth={100} padding="$3" backgroundColor="$green2">
            <YStack alignItems="center">
              <H3>{dashboardData?.threads?.filter(t => t.unread_count > 0)?.length ?? 0}</H3>
              <Text fontSize={12}>Unread Threads</Text>
            </YStack>
          </Card>
          <Card flex={1} minWidth={100} padding="$3" backgroundColor="$orange2">
            <YStack alignItems="center">
              <H3>{dashboardData?.threads?.filter(t => t.status === 'content_pending')?.length ?? 0}</H3>
              <Text fontSize={12}>Pending Content</Text>
            </YStack>
          </Card>
        </XStack>

        {/* Quick-link cards */}
        <XStack gap="$3">
          <Card
            flex={1}
            padding="$3"
            pressStyle={{ opacity: 0.8 }}
            onPress={() => router.push('/(tabs)/(messages)')}
          >
            <YStack alignItems="center" gap="$2">
              <Text fontWeight="bold">View Messages</Text>
              <Text fontSize={12} color="$gray10">Check your threads</Text>
            </YStack>
          </Card>
          <Card
            flex={1}
            padding="$3"
            pressStyle={{ opacity: 0.8 }}
            onPress={() => router.push('/(tabs)/(profile)')}
          >
            <YStack alignItems="center" gap="$2">
              <Text fontWeight="bold">View Profile</Text>
              <Text fontSize={12} color="$gray10">Your creator profile</Text>
            </YStack>
          </Card>
        </XStack>

        {/* Recent activity */}
        <YStack gap="$2">
          <Text fontWeight="bold">Recent Activity</Text>
          {dashboardData?.threads?.slice(0, 3).map((thread) => (
            <Card key={thread.$id} padding="$3">
              <YStack gap="$1">
                <Text fontWeight="bold">{thread.campaign_title}</Text>
                <XStack justifyContent="space-between">
                  <Text fontSize={12} color="$gray10">{thread.status}</Text>
                  <Text fontSize={12} color="$gray10">
                    {thread.unread_count > 0 ? `${thread.unread_count} unread` : ''}
                  </Text>
                </XStack>
              </YStack>
            </Card>
          ))}
          {(!dashboardData?.threads || dashboardData.threads.length === 0) && (
            <Text color="$gray10" fontSize={12}>No recent activity</Text>
          )}
        </YStack>

        {/* Disconnect button */}
        <Button onPress={handleDisconnect} theme="red" marginTop="$4">
          Disconnect Instagram
        </Button>
      </YStack>
    </ScrollView>
  );
}
