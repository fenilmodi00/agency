import { useState, useCallback, useRef } from 'react';
import { useSignIn, useSignUp, useOAuth } from '@clerk/clerk-expo';
import { useRouter } from 'expo-router';

export type AuthMode = 'login' | 'signup';
export type AuthStep = 'idle' | 'otp-sent' | 'verifying' | 'complete' | 'error';

interface AuthState {
  mode: AuthMode;
  step: AuthStep;
  error: string | null;
  isLoading: boolean;
  email: string;
  pendingIdentifier: string | null;
}

interface UseAuthFlowReturn {
  mode: AuthMode;
  step: AuthStep;
  error: string | null;
  isLoading: boolean;
  email: string;
  setMode: (mode: AuthMode) => void;
  submitEmailPassword: (email: string, password: string) => Promise<void>;
  submitEmailOTP: (email: string) => Promise<void>;
  submitOTP: (code: string) => Promise<void>;
  loginWithGoogle: () => Promise<void>;
  resendOTP: () => Promise<void>;
}

function extractClerkError(err: any): string {
  return (
    err.errors?.[0]?.longMessage ||
    err.errors?.[0]?.message ||
    err.longMessage ||
    err.message ||
    'Something went wrong'
  );
}

export function useAuthFlow(): UseAuthFlowReturn {
  const router = useRouter();
  const { signIn, isLoaded: signInLoaded, setActive: setSignInActive } = useSignIn();
  const { signUp, isLoaded: signUpLoaded, setActive: setSignUpActive } = useSignUp();
  const { startOAuthFlow } = useOAuth({ strategy: 'oauth_google' });

  const [state, setState] = useState<AuthState>({
    mode: 'login',
    step: 'idle',
    error: null,
    isLoading: false,
    email: '',
    pendingIdentifier: null,
  });

  const emailRef = useRef('');
  const passwordRef = useRef('');

  const setMode = useCallback((mode: AuthMode) => {
    setState((s) => ({ ...s, mode, step: 'idle', error: null }));
  }, []);

  const setLoading = useCallback((isLoading: boolean) => {
    setState((s) => ({ ...s, isLoading }));
  }, []);

  const setError = useCallback((error: string | null) => {
    setState((s) => ({ ...s, step: error ? 'error' : s.step, error }));
  }, []);

  const navigateToHome = useCallback(() => {
    router.replace('/(tabs)/(home)');
  }, [router]);

  // ─── Email + Password Sign-Up (then OTP verify) ───
  const submitEmailPassword = useCallback(
    async (email: string, password: string) => {
      if (!signUpLoaded) return;
      setLoading(true);
      setError(null);
      emailRef.current = email;
      passwordRef.current = password;

      try {
        const result = await signUp.create({ emailAddress: email, password });

        if (result.status === 'complete') {
          await setSignUpActive({ session: result.createdSessionId });
          setState((s) => ({ ...s, step: 'complete' }));
          navigateToHome();
          return;
        }

        // Send email verification code
        await signUp.prepareEmailAddressVerification({ strategy: 'email_code' });

        setState((s) => ({
          ...s,
          step: 'otp-sent',
          email,
          pendingIdentifier: email,
        }));
      } catch (err: any) {
        setError(extractClerkError(err));
      } finally {
        setLoading(false);
      }
    },
    [signUpLoaded, signUp, setSignUpActive, setLoading, setError, navigateToHome]
  );

  // ─── Email OTP Login (passwordless) ───
  const submitEmailOTP = useCallback(
    async (email: string) => {
      if (!signInLoaded) return;
      setLoading(true);
      setError(null);
      emailRef.current = email;

      try {
        const result = await signIn.create({ identifier: email });

        if (result.status === 'complete') {
          await setSignInActive({ session: result.createdSessionId });
          setState((s) => ({ ...s, step: 'complete' }));
          navigateToHome();
          return;
        }

        const emailCodeFactor = result.supportedFirstFactors?.find(
          (f): f is { strategy: 'email_code'; emailAddressId: string } =>
            f.strategy === 'email_code'
        );
        if (!emailCodeFactor?.emailAddressId) {
          throw new Error('Email code sign-in is not available');
        }

        await result.prepareFirstFactor({
          strategy: 'email_code',
          emailAddressId: emailCodeFactor.emailAddressId,
        });

        setState((s) => ({
          ...s,
          step: 'otp-sent',
          email,
          pendingIdentifier: email,
        }));
      } catch (err: any) {
        setError(extractClerkError(err));
      } finally {
        setLoading(false);
      }
    },
    [signInLoaded, signIn, setSignInActive, setLoading, setError, navigateToHome]
  );

  // ─── Verify OTP (shared for login & sign-up) ───
  const submitOTP = useCallback(
    async (code: string) => {
      if (!signInLoaded && !signUpLoaded) return;
      setLoading(true);
      setError(null);

      try {
        if (state.mode === 'signup' && signUp) {
          const result = await signUp.attemptEmailAddressVerification({ code });

          if (result.status === 'complete') {
            await setSignUpActive({ session: result.createdSessionId });
            setState((s) => ({ ...s, step: 'complete' }));
            navigateToHome();
          } else {
            setState((s) => ({
              ...s,
              step: 'otp-sent',
              error: 'Verification incomplete. Please try again.',
            }));
          }
        } else if (signIn) {
          const result = await signIn.attemptFirstFactor({
            strategy: 'email_code',
            code,
          });

          if (result.status === 'complete') {
            await setSignInActive({ session: result.createdSessionId });
            setState((s) => ({ ...s, step: 'complete' }));
            navigateToHome();
          } else {
            setState((s) => ({
              ...s,
              step: 'otp-sent',
              error: 'Verification incomplete. Please try again.',
            }));
          }
        }
      } catch (err: any) {
        setState((s) => ({
          ...s,
          step: 'otp-sent',
          error: extractClerkError(err),
        }));
      } finally {
        setLoading(false);
      }
    },
    [
      state.mode,
      signInLoaded,
      signUpLoaded,
      signIn,
      signUp,
      setSignInActive,
      setSignUpActive,
      setLoading,
      setError,
      navigateToHome,
    ]
  );

  // ─── Resend OTP ───
  const resendOTP = useCallback(async () => {
    if (!emailRef.current) return;
    setLoading(true);
    setError(null);

    try {
      if (state.mode === 'signup' && signUp) {
        await signUp.prepareEmailAddressVerification({ strategy: 'email_code' });
      } else if (signIn) {
        const result = await signIn.create({ identifier: emailRef.current });
        const emailCodeFactor = result.supportedFirstFactors?.find(
          (f): f is { strategy: 'email_code'; emailAddressId: string } =>
            f.strategy === 'email_code'
        );
        if (!emailCodeFactor?.emailAddressId) {
          throw new Error('Email code sign-in is not available');
        }
        await result.prepareFirstFactor({
          strategy: 'email_code',
          emailAddressId: emailCodeFactor.emailAddressId,
        });
      }
    } catch (err: any) {
      setError(extractClerkError(err));
    } finally {
      setLoading(false);
    }
  }, [state.mode, signIn, signUp, setLoading, setError]);

  // ─── Google OAuth ───
  const loginWithGoogle = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const { createdSessionId, setActive } = await startOAuthFlow();
      if (createdSessionId) {
        await setActive!({ session: createdSessionId });
        setState((s) => ({ ...s, step: 'complete' }));
        navigateToHome();
      } else {
        setError('Google sign-in was cancelled');
      }
    } catch (err: any) {
      setError(extractClerkError(err));
    } finally {
      setLoading(false);
    }
  }, [startOAuthFlow, setLoading, setError, navigateToHome]);

  return {
    mode: state.mode,
    step: state.step,
    error: state.error,
    isLoading: state.isLoading,
    email: state.email,
    setMode,
    submitEmailPassword,
    submitEmailOTP,
    submitOTP,
    loginWithGoogle,
    resendOTP,
  };
}
