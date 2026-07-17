// Set required env vars before any module imports
process.env.EXPO_PUBLIC_IG_API_BASE_URL = 'http://localhost:8000';
process.env.EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY = 'pk_test_mock_key';

// Mock @clerk/expo
jest.mock('@clerk/expo', () => ({
  useAuth: () => ({
    isSignedIn: true,
    userId: 'test-user-id',
    getToken: jest.fn().mockResolvedValue('test-token'),
  }),
  useUser: () => ({
    user: {
      id: 'test-user-id',
      firstName: 'Test',
      emailAddresses: [{ emailAddress: 'test@example.com' }],
    },
  }),
  useClerk: () => ({
    signOut: jest.fn().mockResolvedValue(undefined),
  }),
  useSignIn: () => ({
    signIn: {
      create: jest.fn().mockResolvedValue({ status: 'complete' }),
      finalize: jest.fn().mockResolvedValue(undefined),
      status: 'complete',
    },
  }),
  useSignUp: () => ({
    signUp: {
      create: jest.fn().mockResolvedValue({ status: 'missing_requirements' }),
      finalize: jest.fn().mockResolvedValue(undefined),
      status: 'missing_requirements',
      verifications: {
        sendEmailCode: jest.fn().mockResolvedValue(undefined),
        verifyEmailCode: jest.fn().mockResolvedValue(undefined),
      },
    },
  }),
  ClerkProvider: ({ children }: { children: React.ReactNode }) => children,
  ClerkLoaded: ({ children }: { children: React.ReactNode }) => children,
  ClerkLoading: ({ children }: { children: React.ReactNode }) => children,
}));

// Mock expo-router
jest.mock('expo-router', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    back: jest.fn(),
  }),
  useLocalSearchParams: () => ({}),
  Link: ({ children }: { children: React.ReactNode }) => children,
}));

// Mock @/lib/appwrite
jest.mock('@/lib/appwrite', () => ({
  tablesDB: {
    listRows: jest.fn().mockResolvedValue({ rows: [], total: 0 }),
    getRow: jest.fn().mockResolvedValue({}),
    createRow: jest.fn().mockResolvedValue({}),
    updateRow: jest.fn().mockResolvedValue({}),
    deleteRow: jest.fn().mockResolvedValue({}),
  },
  realtime: {
    subscribe: jest.fn().mockReturnValue({
      unsubscribe: jest.fn(),
    }),
  },
  account: {
    createSession: jest.fn().mockResolvedValue({}),
  },
  storage: {},
  client: {},
}));

// Mock @/lib/auth-bridge
jest.mock('@/lib/auth-bridge', () => ({
  createAppwriteSession: jest.fn().mockResolvedValue({}),
}));

// Mock @/lib/realtime
jest.mock('@/lib/realtime', () => ({
  useRealtimeSubscription: jest.fn(),
}));

// Mock @/hooks/useDashboard
jest.mock('@/hooks/useDashboard', () => ({
  useDashboard: () => ({
    data: {
      creator: {
        $id: 'test-creator-id',
        ig_user_id: '12345',
        ig_username: 'test_creator',
        full_name: 'Test Creator',
        language_hint: 'english',
        follower_count: 1500,
        following_count: 500,
        media_count: 50,
        avg_reel_views: 2000,
        avg_views: 2000,
        engagement_rate: 5.2,
        creator_tier: 'micro',
      },
      threads: [],
      deals: [],
    },
    loading: false,
    error: null,
    refresh: jest.fn(),
  }),
}));

// Mock react-native-safe-area-context
jest.mock('react-native-safe-area-context', () => {
  const inset = { top: 0, right: 0, bottom: 0, left: 0 };
  return {
    SafeAreaProvider: ({ children }: { children: React.ReactNode }) => children,
    SafeAreaConsumer: ({ children }: { children: (insets: typeof inset) => React.ReactNode }) => children(inset),
    useSafeAreaInsets: () => inset,
  };
});

// Mock expo-secure-store
jest.mock('expo-secure-store', () => ({
  getItemAsync: jest.fn().mockResolvedValue(null),
  setItemAsync: jest.fn().mockResolvedValue(undefined),
  deleteItemAsync: jest.fn().mockResolvedValue(undefined),
}));

// Mock expo-auth-session
jest.mock('expo-auth-session', () => ({
  useAuthRequest: jest.fn().mockReturnValue([{}, { startAsync: jest.fn() }]),
  makeRedirectUri: jest.fn().mockReturnValue('https://example.com/callback'),
}));

// Mock expo-web-browser
jest.mock('expo-web-browser', () => ({
  openAuthSessionAsync: jest.fn().mockResolvedValue({ type: 'success' }),
}));

// Mock tamagui
jest.mock('tamagui', () => {
  const React = require('react');
  const { Text: RNText, View, ScrollView, Image } = require('react-native');
  
  return {
    createTamagui: jest.fn(() => ({
      config: {},
    })),
    TamaguiProvider: ({ children }: { children: React.ReactNode }) => children,
    YStack: ({ children }: { children: React.ReactNode }) => React.createElement(View, null, children),
    XStack: ({ children }: { children: React.ReactNode }) => React.createElement(View, null, children),
    Stack: ({ children }: { children: React.ReactNode }) => React.createElement(View, null, children),
    Text: ({ children }: { children: React.ReactNode }) => React.createElement(RNText, null, children),
    Button: ({ children }: { children: React.ReactNode }) => React.createElement(View, null, React.createElement(RNText, null, children)),
    Input: () => null,
    H1: ({ children }: { children: React.ReactNode }) => React.createElement(RNText, null, children),
    H2: ({ children }: { children: React.ReactNode }) => React.createElement(RNText, null, children),
    H3: ({ children }: { children: React.ReactNode }) => React.createElement(RNText, null, children),
    H4: ({ children }: { children: React.ReactNode }) => React.createElement(RNText, null, children),
    Paragraph: ({ children }: { children: React.ReactNode }) => React.createElement(RNText, null, children),
    Label: ({ children }: { children: React.ReactNode }) => React.createElement(RNText, null, children),
    ScrollView: ({ children }: { children: React.ReactNode }) => React.createElement(ScrollView, null, children),
    Card: ({ children }: { children: React.ReactNode }) => React.createElement(View, null, children),
    Spinner: () => null,
    Separator: () => null,
    Avatar: () => React.createElement(Image, null),
    Heading: ({ children }: { children: React.ReactNode }) => React.createElement(RNText, null, children),
    Sheet: ({ children }: { children: React.ReactNode }) => React.createElement(View, null, children),
  };
});
