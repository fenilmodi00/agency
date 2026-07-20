import React, { useState } from 'react';
import { useSignIn } from '@clerk/clerk-expo';
import { useRouter } from 'expo-router';
import { YStack, Text, Input, Button, Spinner, H2 } from 'tamagui';

export default function LoginScreen() {
  const { signIn, isLoaded, setActive } = useSignIn();
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  async function handleSignIn() {
    if (!isLoaded) return;
    setIsLoading(true);
    setError(null);
    try {
      const result = await signIn.create({ identifier: email, password });
      if (result.status === 'complete') {
        await setActive({ session: result.createdSessionId });
        router.replace('/(tabs)/(home)');
      }
    } catch (err: any) {
      setError(err.errors?.[0]?.message || 'Sign in failed');
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <YStack flex={1} justifyContent="center" alignItems="center" padding="$4" gap="$4">
      <H2>Sign In</H2>
      <Input
        placeholder="Email"
        value={email}
        onChangeText={setEmail}
        autoCapitalize="none"
        keyboardType="email-address"
        width="100%"
        maxWidth={320}
      />
      <Input
        placeholder="Password"
        value={password}
        onChangeText={setPassword}
        secureTextEntry
        width="100%"
        maxWidth={320}
      />
      {error && <Text color="$red10">{error}</Text>}
      <Button
        onPress={handleSignIn}
        theme="blue"
        disabled={!isLoaded || isLoading}
        width="100%"
        maxWidth={320}
      >
        {isLoading ? <Spinner /> : 'Sign In'}
      </Button>
      <Text
        onPress={() => router.push('/sign-up')}
        color="$blue10"
        cursor="pointer"
      >
        Don't have an account? Sign up
      </Text>
    </YStack>
  );
}
