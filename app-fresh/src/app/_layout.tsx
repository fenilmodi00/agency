import '@/lib/polyfills';
import { Slot } from 'expo-router';
import { ClerkProvider } from '@clerk/clerk-expo';
import { TamaguiProvider } from 'tamagui';
import config from '@/tamagui.config';

const CLERK_PUBLISHABLE_KEY = process.env.EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY;
if (!CLERK_PUBLISHABLE_KEY) {
  throw new Error('EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY is not set. Add it to your .env file.');
}

export default function RootLayout() {
  return (
    <ClerkProvider publishableKey={CLERK_PUBLISHABLE_KEY}>
      <TamaguiProvider config={config} defaultTheme="light">
        <Slot />
      </TamaguiProvider>
    </ClerkProvider>
  );
}
