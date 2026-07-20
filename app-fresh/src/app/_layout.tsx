import '@/lib/polyfills';
import { useEffect, useRef } from 'react';
import { Slot } from 'expo-router';
import { ClerkProvider, useAuth } from '@clerk/clerk-expo';
import { TamaguiProvider, YStack } from 'tamagui';
import config from '@/tamagui.config';
import { createAppwriteSession } from '@/lib/auth-bridge';
import { secureTokenCache } from '@/lib/tokenCache';
import AuthScreen from '@/components/auth/AuthScreen';
import { useClayFonts } from '@/lib/fonts';
import { ClaySpinner } from '@/components/clay/ClaySpinner';

const CLERK_PUBLISHABLE_KEY = process.env.EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY;
if (!CLERK_PUBLISHABLE_KEY) {
  throw new Error('EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY is not set. Add it to your .env file.');
}

function AuthGate() {
  const { isSignedIn, isLoaded, getToken } = useAuth();
  const [fontsLoaded, fontsError] = useClayFonts();
  const appwriteSessionCreated = useRef(false);

  useEffect(() => {
    if (!isLoaded) return;

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

    if (!isSignedIn) {
      appwriteSessionCreated.current = false;
    }
  }, [isSignedIn, isLoaded, getToken]);

  if (!fontsLoaded && !fontsError) {
    return (
      <YStack flex={1} justify="center" items="center" background="$canvas">
        <ClaySpinner size={40} />
      </YStack>
    );
  }

  if (!isLoaded) {
    return (
      <YStack flex={1} justify="center" items="center" background="$canvas">
        <ClaySpinner size={40} label="Loading..." />
      </YStack>
    );
  }

  if (!isSignedIn) {
    // Render auth UI directly — avoids <Redirect /> infinite loop with Tamagui portal
    return <AuthScreen />;
  }

  return <Slot />;
}

export default function RootLayout() {
  return (
    <ClerkProvider publishableKey={CLERK_PUBLISHABLE_KEY} tokenCache={secureTokenCache}>
      <TamaguiProvider config={config} defaultTheme="light">
        <AuthGate />
      </TamaguiProvider>
    </ClerkProvider>
  );
}
