import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: ['class'],
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './lib/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        ui: ['var(--font-ui)'],
        editorial: ['var(--font-editorial)'],
        display: ['var(--font-display)'],
        accent: ['var(--font-accent)'],
        mono: ['var(--font-mono)'],
      },
      colors: {
        ink: '#0B0F14',
        parchment: '#F8FAFC',
        background: '#F8FAFC',
        foreground: '#0B0F14',
        card: '#FFFFFF',
        muted: '#CBD5E1',
        border: '#CBD5E1',
        primary: '#0B0F14',
        'primary-foreground': '#F8FAFC',
        accent: '#CBD5E1',
        success: '#2B6B4A',
        warning: '#AA7A2B',
        error: '#8B3E3E',
        info: '#64748B',
        forecast: '#64748B',
        shell: {
          bg: '#0B0F14',
          surface: '#24303E',
          text: '#F8FAFC',
          muted: '#64748B',
          border: '#24303E',
          active: '#24303E',
          'active-text': '#F8FAFC',
          hover: '#18222E',
        },
      },
      borderRadius: {
        dense: '4px',
        control: '6px',
        panel: '8px',
        dialog: '8px',
        container: '12px',
      },
      boxShadow: {
        card: '0 1px 0 rgba(20,31,26,0.08)',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
};

export default config;
