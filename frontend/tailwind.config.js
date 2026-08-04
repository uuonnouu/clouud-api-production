/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Outfit', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      colors: {
        background: '#0A0B0E',
        surface: '#111318',
        terminal: '#050505',
        primary: '#FFFFFF',
        secondary: '#94A3B8',
        muted: '#64748B',
        accent: {
          green: '#10B981',
          pink: '#EC4899',
          yellow: '#EAB308',
          blue: '#3B82F6',
          cyan: '#00F0FF'
        }
      }
    },
  },
  plugins: [],
}
