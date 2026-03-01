/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Electric Cyan - Primary Accent
        cyber: {
          50: '#E0F7FA',
          100: '#B2EBF2',
          200: '#80DEEA',
          300: '#4DD0E1',
          400: '#26C6DA',
          500: '#00BCD4',
          600: '#00ACC1',
          700: '#0097A7',
          800: '#00838F',
          900: '#006064',
        },
        electric: '#00E5FF',
        
        // Deep Navy - Background System
        navy: {
          50: '#E3F2FD',
          100: '#BBDEFB',
          200: '#90CAF9',
          300: '#64B5F6',
          400: '#42A5F5',
          500: '#2196F3',
          600: '#1E88E5',
          700: '#1976D2',
          800: '#1565C0',
          900: '#0D47A1',
          950: '#0A1929',
          1000: '#061018',
        },
        
        // Steel - Surface System
        steel: {
          50: '#ECEFF1',
          100: '#CFD8DC',
          200: '#B0BEC5',
          300: '#90A4AE',
          400: '#78909C',
          500: '#607D8B',
          600: '#546E7A',
          700: '#455A64',
          800: '#37474F',
          900: '#263238',
          950: '#1A252F',
        },

        // Additional Colors
        tertiary: '#f3f4f6',
        card: '#ffffff',
        background: '#f9fafb',
        accent: '#00E5FF',
        border: '#e5e7eb',
        'border-light': '#f3f4f6',
      },
      fontFamily: {
        display: ['JetBrains Mono', 'monospace'],
        body: ['DM Sans', 'sans-serif'],
        mono: ['IBM Plex Mono', 'monospace'],
      },
      animation: {
        'glow': 'glow 2s ease-in-out infinite',
        'pulse-fast': 'pulse 1s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'slide-up': 'slideUp 0.3s ease-out',
        'slide-in': 'slideIn 0.2s ease-out',
        'fade-in': 'fadeIn 0.15s ease-out',
      },
      keyframes: {
        glow: {
          '0%, 100%': { 
            boxShadow: '0 0 5px rgba(0, 229, 255, 0.3), 0 0 10px rgba(0, 229, 255, 0.3)'
          },
          '50%': { 
            boxShadow: '0 0 10px rgba(0, 229, 255, 0.3), 0 0 20px rgba(0, 229, 255, 0.3), 0 0 30px rgba(0, 229, 255, 0.3)'
          },
        },
        slideUp: {
          from: { opacity: '0', transform: 'translateY(10px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        slideIn: {
          from: { opacity: '0', transform: 'translateX(-10px)' },
          to: { opacity: '1', transform: 'translateX(0)' },
        },
        fadeIn: {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
      },
      boxShadow: {
        'electric': '0 0 10px rgba(0, 229, 255, 0.3), 0 0 20px rgba(0, 229, 255, 0.3)',
        'electric-sm': '0 0 5px rgba(0, 229, 255, 0.3)',
        'success': '0 0 10px rgba(0, 200, 83, 0.3)',
        'error': '0 0 10px rgba(255, 82, 82, 0.3)',
      },
    },
  },
  plugins: [],
}
