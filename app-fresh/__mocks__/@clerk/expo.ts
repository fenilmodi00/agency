// Manual mock for @clerk/expo — avoids the need to install the package for testing
const React = require('react');

module.exports = {
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
      create: jest
        .fn()
        .mockResolvedValue({ status: 'needs_first_factor', supportedFirstFactors: [{ strategy: 'email_code', emailAddressId: 'test-id' }] }),
      prepareFirstFactor: jest.fn().mockResolvedValue(undefined),
      attemptFirstFactor: jest.fn().mockResolvedValue({ status: 'complete', createdSessionId: 'test-session' }),
      status: 'needs_first_factor',
    },
    setActive: jest.fn().mockResolvedValue(undefined),
    isLoaded: true,
  }),
  useSignUp: () => ({
    signUp: {
      create: jest.fn().mockResolvedValue({ status: 'missing_requirements' }),
      prepareEmailAddressVerification: jest.fn().mockResolvedValue(undefined),
      attemptEmailAddressVerification: jest.fn().mockResolvedValue({ status: 'complete', createdSessionId: 'test-session' }),
      status: 'missing_requirements',
    },
    setActive: jest.fn().mockResolvedValue(undefined),
    isLoaded: true,
  }),
  ClerkProvider: ({ children }: { children: any }) => children,
  ClerkLoaded: ({ children }: { children: any }) => children,
  ClerkLoading: ({ children }: { children: any }) => children,
};
