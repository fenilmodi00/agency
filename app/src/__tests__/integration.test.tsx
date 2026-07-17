import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react-native';
import Home from '@/app/(tabs)/(home)/index';
import { loginInstagram, fetchMedia, fetchInsights, disconnectInstagram } from '@/lib/instagram';

const mockLoginInstagram = loginInstagram as jest.Mock;
const mockFetchMedia = fetchMedia as jest.Mock;
const mockFetchInsights = fetchInsights as jest.Mock;
const mockDisconnectInstagram = disconnectInstagram as jest.Mock;

jest.mock('@clerk/clerk-expo', () => ({
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

jest.mock('@/lib/instagram', () => ({
  loginInstagram: jest.fn(),
  fetchMedia: jest.fn(),
  fetchInsights: jest.fn(),
  disconnectInstagram: jest.fn(),
  fetchProfile: jest.fn().mockRejectedValue(new Error('not connected')),
}));

jest.mock('tamagui', () => {
  const React = require('react');
  const { TextInput, Text, View, TouchableOpacity, ActivityIndicator } = require('react-native');

  return {
    YStack: ({ children, ...props }: any) => React.createElement(View, props, children),
    XStack: ({ children, ...props }: any) => React.createElement(View, props, children),
    Text: ({ children, ...props }: any) => React.createElement(Text, props, children),
    Button: ({ children, onPress, ...props }: any) =>
      React.createElement(TouchableOpacity, { onPress, ...props }, React.createElement(Text, null, children)),
    Input: (props: any) => React.createElement(TextInput, props),
    Spinner: () => React.createElement(ActivityIndicator, null),
    H2: ({ children, ...props }: any) => React.createElement(Text, props, children),
  };
});

describe('Integration Tests', () => {
  beforeEach(() => {
    mockLoginInstagram.mockReset();
    mockFetchMedia.mockReset();
    mockFetchInsights.mockReset();
    mockDisconnectInstagram.mockReset();

    mockFetchMedia.mockResolvedValue([]);
    mockFetchInsights.mockResolvedValue({ data: [] });
  });

  describe('Home Screen', () => {
    it('renders login form with username and password inputs and a Connect button', async () => {
      await render(<Home />);

      expect(screen.getByPlaceholderText('Instagram username')).toBeTruthy();
      expect(screen.getByPlaceholderText('Instagram password')).toBeTruthy();
      expect(screen.getByText('Connect')).toBeTruthy();
    });

    it('calls loginInstagram with correct credentials when Connect is pressed', async () => {
      mockLoginInstagram.mockResolvedValue({
        pk: '12345',
        username: 'test_creator',
      });

      await render(<Home />);

      await fireEvent.changeText(screen.getByPlaceholderText('Instagram username'), 'testuser');
      await fireEvent.changeText(screen.getByPlaceholderText('Instagram password'), 'testpass');
      await fireEvent.press(screen.getByText('Connect'));

      await waitFor(() => {
        expect(mockLoginInstagram).toHaveBeenCalledWith('test-user-id', 'testuser', 'testpass');
      });
    });

    it('shows connected badge after successful login', async () => {
      mockLoginInstagram.mockResolvedValue({
        pk: '12345',
        username: 'test_creator',
      });

      await render(<Home />);

      await fireEvent.changeText(screen.getByPlaceholderText('Instagram username'), 'testuser');
      await fireEvent.changeText(screen.getByPlaceholderText('Instagram password'), 'testpass');
      await fireEvent.press(screen.getByText('Connect'));

      await waitFor(() => {
        expect(screen.getByText(/Connected/)).toBeTruthy();
        expect(screen.getByText('@test_creator')).toBeTruthy();
      });
    });

    it('shows error text on login failure', async () => {
      mockLoginInstagram.mockRejectedValue(new Error('Invalid credentials'));

      await render(<Home />);

      await fireEvent.changeText(screen.getByPlaceholderText('Instagram username'), 'testuser');
      await fireEvent.changeText(screen.getByPlaceholderText('Instagram password'), 'testpass');
      await fireEvent.press(screen.getByText('Connect'));

      await waitFor(() => {
        expect(screen.getByText('Invalid Instagram credentials')).toBeTruthy();
      });
    });

    it('shows generic error text on Instagram login failure', async () => {
      mockLoginInstagram.mockRejectedValue(new Error('Instagram login failed'));

      await render(<Home />);

      await fireEvent.changeText(screen.getByPlaceholderText('Instagram username'), 'testuser');
      await fireEvent.changeText(screen.getByPlaceholderText('Instagram password'), 'testpass');
      await fireEvent.press(screen.getByText('Connect'));

      await waitFor(() => {
        expect(
          screen.getByText('Could not connect to Instagram. Check 2FA or try again.')
        ).toBeTruthy();
      });
    });

    it('clears credentials from inputs after successful login', async () => {
      mockLoginInstagram.mockResolvedValue({
        pk: '12345',
        username: 'test_creator',
      });

      await render(<Home />);

      await fireEvent.changeText(screen.getByPlaceholderText('Instagram username'), 'testuser');
      await fireEvent.changeText(screen.getByPlaceholderText('Instagram password'), 'testpass');
      await fireEvent.press(screen.getByText('Connect'));

      await waitFor(() => {
        expect(screen.getByText(/Connected/)).toBeTruthy();
      });

      // After successful login, inputs are cleared from DOM (replaced by Connected badge)
      expect(screen.queryByPlaceholderText('Instagram username')).toBeNull();
      expect(screen.queryByPlaceholderText('Instagram password')).toBeNull();
    });

    it('shows login form again on session_expired error', async () => {
      mockLoginInstagram.mockRejectedValue(new Error('session_expired'));

      await render(<Home />);

      await fireEvent.changeText(screen.getByPlaceholderText('Instagram username'), 'testuser');
      await fireEvent.changeText(screen.getByPlaceholderText('Instagram password'), 'testpass');
      await fireEvent.press(screen.getByText('Connect'));

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Instagram username')).toBeTruthy();
        expect(screen.getByPlaceholderText('Instagram password')).toBeTruthy();
        expect(screen.getByText('Connect')).toBeTruthy();
      });
    });
  });
});
