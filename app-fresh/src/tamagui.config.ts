import { createTamagui } from 'tamagui'
import { defaultConfig } from '@tamagui/config/v5'

const config = createTamagui({
  ...defaultConfig,
  themes: {
    ...defaultConfig.themes,
    light: {
      ...defaultConfig.themes.light,
      background: '#FFFFFF',
      color: '#1A1A1A',
      primary: '#FF6B35',
    },
  },
})

export default config
