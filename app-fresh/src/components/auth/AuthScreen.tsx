import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  TextInput as RNTextInput,
  Pressable,
} from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withTiming,
  Easing,
} from 'react-native-reanimated';
import { Ionicons } from '@expo/vector-icons';
import { View, Text, TextInput } from '@/tw';
import { cn, clayInput } from '@/tw/cn';
import { ClayAnimatedButton } from '@/components/clay/ClayAnimatedButton';
import { useAuthFlow, AuthMode } from '@/hooks/useAuthFlow';
import { useShakeAnimation } from '@/hooks/useClayAnimations';

const TOGGLE_WIDTH = 280;
const PILL_WIDTH = TOGGLE_WIDTH / 2 - 4;
const INPUT_HEIGHT = 44;
const CLAY = {
  canvas: '#fffaf0',
  primary: '#0a0a0a',
  surfaceCard: '#f5f0e0',
  hairline: '#e5e5e5',
  ink: '#0a0a0a',
  muted: '#6a6a6a',
  mutedSoft: '#9a9a9a',
  bodyStrong: '#1a1a1a',
  error: '#ef4444',
  brandTeal: '#1a3a3a',
} as const;

// ─── Capsule Toggle ───
function CapsuleToggle({ mode, onChange }: { mode: AuthMode; onChange: (m: AuthMode) => void }) {
  const translateX = useSharedValue(mode === 'login' ? 0 : PILL_WIDTH);

  useEffect(() => {
    translateX.value = withTiming(mode === 'login' ? 0 : PILL_WIDTH, {
      duration: 250,
      easing: Easing.out(Easing.cubic),
    });
  }, [mode, translateX]);

  const pillStyle = useAnimatedStyle(() => ({
    transform: [{ translateX: translateX.value }],
  }));

  return (
    <View style={{
      width: TOGGLE_WIDTH, height: 44, backgroundColor: CLAY.surfaceCard,
      borderRadius: 9999, flexDirection: 'row', alignItems: 'center', padding: 4, alignSelf: 'center',
    }}>
      <Animated.View style={[{
        position: 'absolute', left: 4, width: PILL_WIDTH, height: 36,
        backgroundColor: CLAY.primary, borderRadius: 9999,
      }, pillStyle]} />
      {(['login', 'signup'] as AuthMode[]).map((m) => (
        <Pressable key={m} onPress={() => onChange(m)}
          style={{ flex: 1, height: 36, alignItems: 'center', justifyContent: 'center', zIndex: 1 }}>
          <Text className="text-sm font-semibold" style={{ color: mode === m ? 'white' : CLAY.bodyStrong }}>
            {m === 'login' ? 'Log In' : 'Sign Up'}
          </Text>
        </Pressable>
      ))}
    </View>
  );
}

// ─── Password Input with eye icon ───
function PasswordInput({ value, onChangeText }: { value: string; onChangeText: (v: string) => void }) {
  const [visible, setVisible] = useState(false);
  return (
    <View style={{ position: 'relative', width: '100%', height: INPUT_HEIGHT }}>
      <TextInput
        placeholder="Password (min 8 characters)" value={value} onChangeText={onChangeText}
        secureTextEntry={!visible} autoCapitalize="none" autoComplete="new-password"
        textContentType="newPassword" placeholderTextColor={CLAY.mutedSoft}
        className={cn(clayInput, 'w-full pr-12')}
      />
      <Pressable onPress={() => setVisible(v => !v)}
        style={{ position: 'absolute', right: 12, top: 0, bottom: 0, width: 40, alignItems: 'center', justifyContent: 'center' }}
        accessibilityLabel={visible ? 'Hide password' : 'Show password'}>
        <Ionicons name={visible ? 'eye-off' : 'eye'} size={20} color={CLAY.muted} />
      </Pressable>
    </View>
  );
}

// ─── OTP Input ───
function OTPInput({ value, onChange, disabled }: { value: string; onChange: (c: string) => void; disabled: boolean }) {
  const inputs = useRef<(RNTextInput | null)[]>([]);
  const digits = value.split('');
  while (digits.length < 6) digits.push('');

  function handleChange(text: string, index: number) {
    if (disabled) return;
    const clean = text.replace(/\D/g, '').slice(-1);
    const newDigits = [...digits];
    newDigits[index] = clean;
    onChange(newDigits.join('').slice(0, 6));
    if (clean && index < 5) inputs.current[index + 1]?.focus();
  }

  function handleKeyPress(e: any, index: number) {
    if (e.nativeEvent.key === 'Backspace' && !digits[index] && index > 0) {
      inputs.current[index - 1]?.focus();
    }
  }

  return (
    <View style={{ flexDirection: 'row', gap: 8, justifyContent: 'center' }}>
      {digits.map((digit, index) => (
        <View key={index} style={{
          width: 48, height: 56, borderRadius: 12, borderWidth: 2,
          borderColor: digit ? CLAY.primary : CLAY.hairline,
          backgroundColor: CLAY.canvas, justifyContent: 'center', alignItems: 'center',
        }}>
          <RNTextInput
            ref={(ref) => { inputs.current[index] = ref; }}
            value={digit} onChangeText={(text) => handleChange(text, index)}
            onKeyPress={(e) => handleKeyPress(e, index)}
            keyboardType="number-pad" maxLength={1} editable={!disabled} selectTextOnFocus
            style={{ width: 48, height: 56, textAlign: 'center', fontSize: 22, fontWeight: '600', color: CLAY.ink }}
          />
        </View>
      ))}
    </View>
  );
}

// ─── Main Auth Screen ───
export default function AuthScreen() {
  const {
    mode, step, error, isLoading, email: otpEmail,
    setMode, submitEmailPassword, submitEmailOTP, submitOTP, loginWithGoogle, resendOTP,
  } = useAuthFlow();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [otpCode, setOtpCode] = useState('');
  const [resendTimer, setResendTimer] = useState(30);
  const [autoSubmitting, setAutoSubmitting] = useState(false);

  const showOTP = step === 'otp-sent';
  const showPassword = mode === 'signup';

  // Crossfade opacities
  const loginOpacity = useSharedValue(1);
  const signupOpacity = useSharedValue(0);
  const passwordHeight = useSharedValue(0);
  const passwordOpacity = useSharedValue(0);

  useEffect(() => {
    if (showOTP) setResendTimer(30);
  }, [showOTP]);

  useEffect(() => {
    if (!showOTP || resendTimer <= 0) return;
    const interval = setInterval(() => setResendTimer(t => t - 1), 1000);
    return () => clearInterval(interval);
  }, [showOTP, resendTimer]);

  // Animate crossfades
  useEffect(() => {
    if (showOTP) return;
    loginOpacity.value = withTiming(mode === 'login' ? 1 : 0, { duration: 200 });
    signupOpacity.value = withTiming(mode === 'signup' ? 1 : 0, { duration: 200 });
  }, [mode, showOTP, loginOpacity, signupOpacity]);

  useEffect(() => {
    passwordHeight.value = withTiming(showPassword ? INPUT_HEIGHT : 0, { duration: 300 });
    passwordOpacity.value = withTiming(showPassword ? 1 : 0, { duration: 300 });
  }, [showPassword, passwordHeight, passwordOpacity]);

  const loginFadeStyle = useAnimatedStyle(() => ({ opacity: loginOpacity.value }));
  const signupFadeStyle = useAnimatedStyle(() => ({ opacity: signupOpacity.value }));
  const passwordContainerStyle = useAnimatedStyle(() => ({
    height: passwordHeight.value,
    opacity: passwordOpacity.value,
  }));

  // Shake for OTP errors
  const { shake, animatedStyle: shakeStyle } = useShakeAnimation();
  useEffect(() => {
    if (error && showOTP) shake();
  }, [error, showOTP, shake]);

  const handleContinue = useCallback(async () => {
    if (mode === 'signup') await submitEmailPassword(email, password);
    else await submitEmailOTP(email);
  }, [mode, email, password, submitEmailPassword, submitEmailOTP]);

  const handleVerify = useCallback(async () => {
    if (otpCode.length !== 6 || isLoading) return;
    await submitOTP(otpCode);
  }, [otpCode, isLoading, submitOTP]);

  // Auto-verify: submit when 6 digits entered (300ms debounce so the last digit renders first)
  useEffect(() => {
    if (otpCode.length === 6 && !isLoading && !autoSubmitting) {
      setAutoSubmitting(true);
      const timer = setTimeout(() => {
        handleVerify();
      }, 300);
      return () => clearTimeout(timer);
    }
    if (otpCode.length < 6) {
      setAutoSubmitting(false);
    }
  }, [otpCode, isLoading, autoSubmitting, handleVerify]);

  const handleResend = useCallback(async () => {
    await resendOTP();
    setResendTimer(30);
  }, [resendOTP]);

  const isValidEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  const canSubmit = isValidEmail && !isLoading && (mode === 'login' || password.length >= 8);

  // ─── OTP VIEW ───
  if (showOTP) {
    return (
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={{ flex: 1 }}>
        <View className="flex-1 bg-canvas items-center px-6" style={{ paddingTop: 100 }}>
          <View className="w-full max-w-[400px] items-center gap-6">
            {/* OTP Header */}
            <View className="items-center gap-3 max-w-[320px]">
              <Text className="text-title-lg font-semibold text-ink tracking-[-0.3px] text-center">
                Verify your email
              </Text>
              <Text className="text-body-sm text-muted text-center" style={{ lineHeight: 22 }}>
                Enter the 6-digit code sent to{' '}
                <Text className="font-semibold text-body-strong">{otpEmail || 'your email'}</Text>
              </Text>
            </View>

            {/* OTP Input */}
            <Animated.View className="w-full" style={shakeStyle}>
              <OTPInput value={otpCode} onChange={setOtpCode} disabled={isLoading} />
            </Animated.View>

            {/* Auto-submit indicator */}
            {autoSubmitting && !error && (
              <Text className="text-caption text-muted-soft">Verifying automatically...</Text>
            )}

            {/* Error */}
            {error && (
              <Text className="text-error text-sm text-center max-w-[320px] leading-5">{error}</Text>
            )}

            {/* Manual Verify Button */}
            <View className="w-full max-w-[320px]">
              <ClayAnimatedButton
                variant="primary"
                onPress={handleVerify}
                disabled={otpCode.length !== 6 || isLoading}
                loading={isLoading && !autoSubmitting}
                fullWidth
              >
                Verify & Continue
              </ClayAnimatedButton>
            </View>

            {/* Resend */}
            <View className="items-center gap-3">
              <Text className="text-caption text-muted">Didn't receive the code?</Text>
              {resendTimer > 0 ? (
                <Text className="text-caption text-muted-soft">Resend in {resendTimer}s</Text>
              ) : (
                <Pressable onPress={handleResend}>
                  <Text className="text-caption text-brand-teal font-semibold">Resend code</Text>
                </Pressable>
              )}
            </View>

            {/* Go back */}
            <Pressable onPress={() => { setOtpCode(''); setMode(mode); }}>
              <Text className="text-caption text-muted">← Change email</Text>
            </Pressable>
          </View>
        </View>
      </KeyboardAvoidingView>
    );
  }

  // ─── FORM VIEW ───
  return (
    <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={{ flex: 1 }}>
      <View className="flex-1 bg-canvas items-center px-6" style={{ paddingTop: 80 }}>
        <View className="w-full max-w-[400px] items-center gap-5">
          {/* Brand */}
          <View className="items-center gap-1.5">
            <Text className="text-display-sm font-medium text-ink tracking-[-0.5px] text-center">
              Creator Workspace
            </Text>
            <View style={{ height: 44, alignItems: 'center', justifyContent: 'center' }}>
              <Animated.View style={[{ position: 'absolute', alignItems: 'center' }, loginFadeStyle]}>
                <Text className="text-body-md text-muted text-center leading-6">
                  Welcome back! Sign in to continue.
                </Text>
              </Animated.View>
              <Animated.View style={[{ position: 'absolute', alignItems: 'center' }, signupFadeStyle]}>
                <Text className="text-body-md text-muted text-center leading-6">
                  Create your account to get started.
                </Text>
              </Animated.View>
            </View>
          </View>

          {/* Toggle */}
          <CapsuleToggle mode={mode} onChange={setMode} />

          {/* Form */}
          <View className="w-full max-w-[320px] items-center gap-3">
            {/* Email */}
            <View className="w-full">
              <TextInput
                placeholder="Email address" value={email} onChangeText={setEmail}
                autoCapitalize="none" keyboardType="email-address" autoComplete="email"
                textContentType="emailAddress" placeholderTextColor={CLAY.mutedSoft}
                className={cn(clayInput, 'w-full')}
              />
            </View>

            {/* Password */}
            <Animated.View style={[{ width: '100%', overflow: 'hidden' }, passwordContainerStyle]}>
              <PasswordInput value={password} onChangeText={setPassword} />
            </Animated.View>

            {/* Error */}
            {error && (
              <Text className="text-error text-sm text-center max-w-[320px] leading-5">{error}</Text>
            )}

            {/* Submit */}
            <Pressable
              onPress={handleContinue}
              disabled={!canSubmit}
              style={{ width: '100%', maxWidth: 320, opacity: canSubmit ? 1 : 0.5 }}
            >
              <View className="h-11 rounded-md bg-primary items-center justify-center">
                {isLoading ? (
                  <ActivityIndicator size="small" color="#ffffff" />
                ) : (
                  <View className="h-5 items-center justify-center">
                    <Animated.View style={[{ position: 'absolute' }, loginFadeStyle]}>
                      <Text className="text-button font-semibold text-on-primary">Continue with Email</Text>
                    </Animated.View>
                    <Animated.View style={[{ position: 'absolute' }, signupFadeStyle]}>
                      <Text className="text-button font-semibold text-on-primary">Create Account</Text>
                    </Animated.View>
                  </View>
                )}
              </View>
            </Pressable>
          </View>

          {/* Divider */}
          <View className="w-full max-w-[320px] flex-row items-center gap-4">
            <View className="flex-1 h-px bg-hairline" />
            <Text className="text-caption text-muted-soft">or</Text>
            <View className="flex-1 h-px bg-hairline" />
          </View>

          {/* Google */}
          <View className="w-full max-w-[320px]">
            <ClayAnimatedButton
              variant="secondary"
              onPress={loginWithGoogle}
              disabled={isLoading}
              loading={isLoading}
              fullWidth
            >
              Continue with Google
            </ClayAnimatedButton>
          </View>

          {/* Helper */}
          <View className="h-9 items-center justify-center">
            <Animated.View style={[{ position: 'absolute', alignItems: 'center', paddingHorizontal: 24 }, loginFadeStyle]}>
              <Text className="text-caption text-muted-soft text-center">
                We'll send you a verification code to sign in.
              </Text>
            </Animated.View>
            <Animated.View style={[{ position: 'absolute', alignItems: 'center', paddingHorizontal: 24 }, signupFadeStyle]}>
              <Text className="text-caption text-muted-soft text-center">
                By signing up, you agree to our Terms and Privacy Policy.
              </Text>
            </Animated.View>
          </View>
        </View>
      </View>
    </KeyboardAvoidingView>
  );
}
