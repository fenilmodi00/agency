import { createFont, createTamagui } from 'tamagui'
import { defaultConfig } from '@tamagui/config/v5'

const clayTokens = {
  color: {
    canvas: '#fffaf0',
    primary: '#0a0a0a',
    'brand-pink': '#ff4d8b',
    'brand-teal': '#1a3a3a',
    'brand-lavender': '#b8a4ed',
    'brand-peach': '#ffb084',
    'brand-ochre': '#e8b94a',
    'brand-mint': '#a4d4c5',
    'brand-coral': '#ff6b5a',
    'surface-soft': '#faf5e8',
    'surface-card': '#f5f0e0',
    'surface-strong': '#ebe6d6',
    'surface-dark': '#0a1a1a',
    'surface-dark-elevated': '#1a2a2a',
    hairline: '#e5e5e5',
    ink: '#0a0a0a',
    'body-strong': '#1a1a1a',
    body: '#3a3a3a',
    muted: '#6a6a6a',
    'muted-soft': '#9a9a9a',
    'on-primary': '#ffffff',
    'on-dark': '#ffffff',
    success: '#22c55e',
    warning: '#f59e0b',
    error: '#ef4444',
  },
  radius: {
    xs: 6,
    sm: 8,
    md: 12,
    lg: 16,
    xl: 24,
    pill: 9999,
    full: 9999,
  },
  space: {
    xxs: 4,
    xs: 8,
    sm: 12,
    md: 16,
    lg: 24,
    xl: 32,
    xxl: 48,
    section: 96,
  },
  size: {
    xxs: 4,
    xs: 8,
    sm: 12,
    md: 16,
    lg: 24,
    xl: 32,
    xxl: 48,
    section: 96,
  },
  zIndex: {
    '0': 0,
    '1': 100,
    '2': 200,
    '3': 300,
    '4': 400,
    '5': 500,
  },
}

const clayFont = createFont({
  family: 'Inter',
  size: {
    'display-xl': 72, 'display-lg': 56, 'display-md': 40, 'display-sm': 32,
    'title-lg': 24, 'title-md': 18, 'title-sm': 16,
    'body-md': 16, 'body-sm': 14,
    'caption': 13, 'caption-uppercase': 12,
    'button': 14, 'nav-link': 14,
  },
  weight: {
    'display-xl': '500', 'display-lg': '500', 'display-md': '500', 'display-sm': '500',
    'title-lg': '600', 'title-md': '600', 'title-sm': '600',
    'body-md': '400', 'body-sm': '400',
    'caption': '500', 'caption-uppercase': '600',
    'button': '600', 'nav-link': '500',
  },
  letterSpacing: {
    'display-xl': -2.5, 'display-lg': -2, 'display-md': -1, 'display-sm': -0.5,
    'title-lg': -0.3, 'title-md': 0, 'title-sm': 0,
    'body-md': 0, 'body-sm': 0,
    'caption': 0, 'caption-uppercase': 1.5,
    'button': 0, 'nav-link': 0,
  },
  lineHeight: {
    'display-xl': 72, 'display-lg': 59, 'display-md': 44, 'display-sm': 37,
    'title-lg': 31, 'title-md': 25, 'title-sm': 22,
    'body-md': 25, 'body-sm': 22,
    'caption': 18, 'caption-uppercase': 17,
    'button': 14, 'nav-link': 20,
  },
})

const config = createTamagui({
  ...defaultConfig,
  fonts: { heading: clayFont, body: clayFont },
  tokens: {
    ...defaultConfig.tokens,
    color: {
      ...clayTokens.color,
    },
    radius: {
      ...defaultConfig.tokens.radius,
      ...clayTokens.radius,
    },
    space: {
      ...defaultConfig.tokens.space,
      ...clayTokens.space,
    },
    size: {
      ...defaultConfig.tokens.size,
      ...clayTokens.size,
    },
    zIndex: {
      ...defaultConfig.tokens.zIndex,
      ...clayTokens.zIndex,
    },
  },
  themes: {
    ...defaultConfig.themes,
    light: {
      ...defaultConfig.themes.light,
      background: clayTokens.color.canvas,
      color: clayTokens.color.ink,
      primary: clayTokens.color.primary,
      borderColor: clayTokens.color.hairline,
      // Map semantic colors for Tamagui component defaults
      blue1: clayTokens.color['surface-soft'],
      blue2: clayTokens.color['surface-card'],
      blue10: clayTokens.color['brand-teal'],
      red1: '#fef2f2',
      red2: '#fee2e2',
      red10: clayTokens.color.error,
      green1: '#f0fdf4',
      green2: '#dcfce7',
      green10: clayTokens.color.success,
      orange1: '#fff7ed',
      orange2: '#ffedd5',
      orange10: clayTokens.color['brand-ochre'],
      purple1: '#faf5ff',
      purple2: '#f3e8ff',
      purple10: clayTokens.color['brand-lavender'],
      yellow1: '#fefce8',
      yellow2: '#fef9c3',
      yellow10: clayTokens.color.warning,
      gray1: clayTokens.color.canvas,
      gray2: clayTokens.color['surface-soft'],
      gray5: clayTokens.color['surface-card'],
      gray10: clayTokens.color.muted,
    },
  },
})

export type Conf = typeof config

declare module 'tamagui' {
  interface TamaguiCustomConfig extends Conf {}
}

export default config
