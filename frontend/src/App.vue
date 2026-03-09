<script setup lang="ts">
import { NConfigProvider, NMessageProvider, darkTheme } from 'naive-ui'
import type { GlobalThemeOverrides } from 'naive-ui'

const themeOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#6366F1',
    primaryColorHover: '#8B5CF6',
    primaryColorPressed: '#4F46E5',
    primaryColorSuppl: '#A78BFA',
    bodyColor: '#0F172A',
    cardColor: '#1E293B',
    modalColor: '#1E293B',
    popoverColor: '#1E293B',
    tableColor: '#1E293B',
    inputColor: 'rgba(255, 255, 255, 0.05)',
    borderColor: 'rgba(255, 255, 255, 0.1)',
    textColorBase: '#F8FAFC',
    textColor1: '#F8FAFC',
    textColor2: '#CBD5E1',
    textColor3: '#94A3B8',
  },
  Button: {
    colorPrimary: '#6366F1',
    colorHoverPrimary: '#8B5CF6',
    colorPressedPrimary: '#4F46E5',
    textColorPrimary: '#FFFFFF',
  },
  Card: {
    color: 'rgba(255, 255, 255, 0.05)',
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  Input: {
    color: 'rgba(255, 255, 255, 0.05)',
    borderColor: 'rgba(255, 255, 255, 0.1)',
    borderHover: 'rgba(99, 102, 241, 0.5)',
    borderFocus: 'rgba(99, 102, 241, 0.7)',
  },
}
</script>

<template>
  <NConfigProvider :theme="darkTheme" :theme-overrides="themeOverrides">
    <NMessageProvider>
      <router-view />
    </NMessageProvider>
  </NConfigProvider>
</template>
