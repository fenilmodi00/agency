import React, { useState, useEffect } from 'react';
import { YStack, Text, Button, Spinner, H2, XStack, Input } from 'tamagui';
import { useUser } from '@clerk/clerk-expo';
import {
  loginInstagram,
  disconnectInstagram,
  fetchMedia,
  fetchInsights,
  fetchProfile,
} from '@/lib/instagram';

export default function HomeScreen() {
  const { user } = useUser();
  const [isConnected, setIsConnected] = useState(false);
  const [username, setUsername] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [igUsername, setIgUsername] = useState('');
  const [igPassword, setIgPassword] = useState('');

  useEffect(() => {
    async function checkConnection() {
      if (!user) return;
      try {
        const profile = await fetchProfile();
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
      const profile = await loginInstagram(user.id, igUsername, igPassword);
      setIsConnected(true);
      setUsername(profile.username);
      setIgUsername('');
      setIgPassword('');
      try { await fetchMedia(); } catch { /* non-critical */ }
      try { await fetchInsights(); } catch { /* non-critical */ }
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
      await disconnectInstagram();
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

  return (
    <YStack flex={1} justifyContent="center" alignItems="center" padding="$4" gap="$4">
      <H2 textAlign="center">Welcome to Creator Workspace</H2>

      {isLoading && (
        <YStack alignItems="center" gap="$2">
          <Spinner size="large" color="$blue10" />
          <Text>Connecting to Instagram...</Text>
        </YStack>
      )}

      {!isLoading && !isConnected && (
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
      )}

      {!isLoading && isConnected && (
        <XStack alignItems="center" gap="$3">
          <Text fontWeight="bold" color="$green10">Connected</Text>
          <Text fontWeight="bold">@{username}</Text>
          <Button size="$2" onPress={handleDisconnect} theme="red">
            Disconnect
          </Button>
        </XStack>
      )}

      {error && (
        <Text color="$red10" textAlign="center" fontSize={12}>
          {error}
        </Text>
      )}
    </YStack>
  );
}
