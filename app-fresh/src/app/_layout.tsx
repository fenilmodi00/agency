import '@/global.css';
import '@/lib/polyfills';
import { useEffect, useRef } from 'react';
import { Slot } from 'expo-router';
import { ClerkProvider, useAuth } from '@clerk/clerk-expo';
import { createAppwriteSession } from '@/lib/auth-bridge';
import { secureTokenCache } from '@/lib/tokenCache';
import AuthScreen from '@/components/auth/AuthScreen';
import { useClayFonts } from '@/lib/fonts';
import { ClaySpinner } from '@/components/clay/ClaySpinner';
import { View } from '@/tw';

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
      <View className="flex-1 items-center justify-center bg-canvas">
        <ClaySpinner size={40} />
      </View>
    );
  }

  if (!isLoaded) {
    return (
      <View className="flex-1 items-center justify-center bg-canvas">
        <ClaySpinner size={40} label="Loading..." />
      </View>
    );
  }

  if (!isSignedIn) {
    // Render auth UI directly — avoids <Redirect /> infinite loop
    return <AuthScreen />;
  }

  return <Slot />;
}

export default function RootLayout() {
  return (
    <ClerkProvider publishableKey={CLERK_PUBLISHABLE_KEY} tokenCache={secureTokenCache}>
      <AuthGate />
    </ClerkProvider>
  );
}
