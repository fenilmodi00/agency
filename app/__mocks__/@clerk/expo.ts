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
  ClerkProvider: ({ children }) => children,
  ClerkLoaded: ({ children }) => children,
  ClerkLoading: ({ children }) => children,
};
