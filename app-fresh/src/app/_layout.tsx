import '@/lib/polyfills';
import { useEffect, useRef } from 'react';
import { Slot } from 'expo-router';
import { ClerkProvider, useAuth } from '@clerk/clerk-expo';
import { TamaguiProvider, YStack, Spinner } from 'tamagui';
import config from '@/tamagui.config';
import { createAppwriteSession } from '@/lib/auth-bridge';
import LoginScreen from './login';

const CLERK_PUBLISHABLE_KEY = process.env.EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY;
if (!CLERK_PUBLISHABLE_KEY) {
  throw new Error('EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY is not set. Add it to your .env file.');
}

function AuthGate() {
  const { isSignedIn, isLoaded, getToken } = useAuth();
  const appwriteSessionCreated = useRef(false);

  useEffect(() => {
    if (isSignedIn && !appwriteSessionCreated.current) {
      appwriteSessionCreated.current = true;
      (async () => {
        try {
          const token = await getToken();
          if (token) {
            await createAppwriteSession(token);
          }
        } catch (err) {
          console.warn('Failed to create Appwrite session:', err);
        }
      })();
    }
  }, [isSignedIn, getToken]);

  if (!isLoaded) {
    return (
      <YStack flex={1} justifyContent="center" alignItems="center">
        <Spinner size="large" />
      </YStack>
    );
  }

  if (!isSignedIn) {
    return <LoginScreen />;
  }

  return <Slot />;
}

export default function RootLayout() {
  return (
    <ClerkProvider publishableKey={CLERK_PUBLISHABLE_KEY}>
      <TamaguiProvider config={config} defaultTheme="light">
        <AuthGate />
      </TamaguiProvider>
    </ClerkProvider>
  );
}
