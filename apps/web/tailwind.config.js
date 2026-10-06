/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ops: {
          bg: '#0B0F0D',
          subtle: '#111713',
          panel: '#151B17',
          surface: '#1B221D',
          hover: '#222B24',
          border: 'rgba(255, 255, 255, 0.08)',
          'border-strong': 'rgba(255, 255, 255, 0.16)',
        },
        forest: {
          DEFAULT: '#3F7D58',
          hover: '#4C9167',
          active: '#35694A',
          subtle: 'rgba(63, 125, 88, 0.16)',
          border: 'rgba(63, 125, 88, 0.35)',
        },
        amber: {
          DEFAULT: '#D99A2B',
          hover: '#E5A638',
          subtle: 'rgba(217, 154, 43, 0.16)',
          border: 'rgba(217, 154, 43, 0.35)',
        },
        danger: {
          DEFAULT: '#D84A3A',
          hover: '#E3594A',
          subtle: 'rgba(216, 74, 58, 0.16)',
          border: 'rgba(216, 74, 58, 0.35)',
        },
        txt: {
          primary: '#F1F3EE',
          secondary: '#AAB3AA',
          muted: '#737C74',
        },
        risk: {
          low: '#3F7D58',
          moderate: '#D99A2B',
          high: '#E06D2E',
          extreme: '#D84A3A',
        },
      },
    },
  },
  plugins: [],
}
