import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: ['class'],
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
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
      fontSize: {
        '2xs': ['var(--text-2xs)', { lineHeight: '1.4' }],
        'xs': ['var(--text-xs)', { lineHeight: '1.4' }],
        'sm': ['var(--text-sm)', { lineHeight: '1.45' }],
        'base': ['var(--text-base)', { lineHeight: '1.5' }],
        'md': ['var(--text-md)', { lineHeight: '1.5' }],
        'lg': ['var(--text-lg)', { lineHeight: '1.5' }],
        'xl': ['var(--text-xl)', { lineHeight: '1.3' }],
        '2xl': ['var(--text-2xl)', { lineHeight: '1.25' }],
        '3xl': ['var(--text-3xl)', { lineHeight: '1.2' }],
        '4xl': ['var(--text-4xl)', { lineHeight: '1.15' }],
      },
      fontWeight: {
        regular: 'var(--weight-regular)',
        medium: 'var(--weight-medium)',
        semibold: 'var(--weight-semibold)',
      },
      borderRadius: {
        dense: 'var(--radius-dense)',
        control: 'var(--radius-control)',
        panel: 'var(--radius-panel)',
        dialog: 'var(--radius-dialog)',
        container: 'var(--radius-container)',
        lg: 'var(--radius-lg)',
        md: 'var(--radius-md)',
        sm: 'var(--radius-sm)',
        xl: 'var(--radius-xl)',
      },
      colors: {
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        chart: {
          '1': 'hsl(var(--success))',
          '2': 'hsl(var(--warning))',
          '3': 'hsl(var(--info))',
          '4': 'hsl(var(--forecast))',
          '5': 'hsl(var(--error))',
        },
        shell: {
          bg: 'hsl(var(--shell-bg))',
          surface: 'hsl(var(--shell-surface))',
          text: 'hsl(var(--shell-text))',
          muted: 'hsl(var(--shell-text-muted))',
          border: 'hsl(var(--shell-border))',
          active: 'hsl(var(--shell-active))',
          'active-text': 'hsl(var(--shell-active-text))',
          hover: 'hsl(var(--shell-hover))',
        },
        success: {
          DEFAULT: 'hsl(var(--success))',
          foreground: 'hsl(var(--success-foreground))',
          muted: 'hsl(var(--success-muted))',
          border: 'hsl(var(--success-border))',
        },
        warning: {
          DEFAULT: 'hsl(var(--warning))',
          foreground: 'hsl(var(--warning-foreground))',
          muted: 'hsl(var(--warning-muted))',
          border: 'hsl(var(--warning-border))',
        },
        error: {
          DEFAULT: 'hsl(var(--error))',
          foreground: 'hsl(var(--error-foreground))',
          muted: 'hsl(var(--error-muted))',
          border: 'hsl(var(--error-border))',
        },
        info: {
          DEFAULT: 'hsl(var(--info))',
          foreground: 'hsl(var(--info-foreground))',
          muted: 'hsl(var(--info-muted))',
          border: 'hsl(var(--info-border))',
        },
        forecast: {
          DEFAULT: 'hsl(var(--forecast))',
          foreground: 'hsl(var(--forecast-foreground))',
          muted: 'hsl(var(--forecast-muted))',
          border: 'hsl(var(--forecast-border))',
        },
        ink: 'hsl(var(--color-ink))',
        slate: 'hsl(var(--color-slate))',
        steel: 'hsl(var(--color-steel))',
        mist: 'hsl(var(--color-mist))',
        paper: 'hsl(var(--color-paper))',
      },
      boxShadow: {
        popover: 'var(--shadow-popover)',
        dialog: 'var(--shadow-dialog)',
        command: 'var(--shadow-command)',
      },
      transitionDuration: {
        fast: 'var(--duration-fast)',
        normal: 'var(--duration-normal)',
        slow: 'var(--duration-slow)',
      },
      transitionTimingFunction: {
        standard: 'var(--ease-standard)',
        enter: 'var(--ease-enter)',
        exit: 'var(--ease-exit)',
      },
      zIndex: {
        sidebar: 'var(--z-sidebar)',
        topbar: 'var(--z-topbar)',
        dropdown: 'var(--z-dropdown)',
        popover: 'var(--z-popover)',
        dialog: 'var(--z-dialog)',
        command: 'var(--z-command)',
        toast: 'var(--z-toast)',
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic':
          'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
      },
      keyframes: {
        'accordion-down': {
          from: { height: '0' },
          to: { height: 'var(--radix-accordion-content-height)' },
        },
        'accordion-up': {
          from: { height: 'var(--radix-accordion-content-height)' },
          to: { height: '0' },
        },
        'fade-in': {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        'fade-out': {
          from: { opacity: '1' },
          to: { opacity: '0' },
        },
        'slide-in-right': {
          from: { transform: 'translateX(100%)' },
          to: { transform: 'translateX(0)' },
        },
        'slide-out-right': {
          from: { transform: 'translateX(0)' },
          to: { transform: 'translateX(100%)' },
        },
      },
      animation: {
        'accordion-down': 'accordion-down 0.2s ease-out',
        'accordion-up': 'accordion-up 0.2s ease-out',
        'fade-in': 'fade-in var(--duration-normal) var(--ease-enter)',
        'fade-out': 'fade-out var(--duration-fast) var(--ease-exit)',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
};
export default config;
