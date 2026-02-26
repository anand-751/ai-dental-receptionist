/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}'
  ],
  theme: {
    extend: {
      animation: {
        'spin-slow': 'spin 6s linear infinite',
        'pulse-slow': 'pulse 2.5s ease-in-out infinite',
        'float': 'float 3s ease-in-out infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        }
      }
    }
  },
  safelist: [
    // Backgrounds
    "from-blue-400", "to-cyan-400",
    "from-green-500", "to-emerald-400",
    "from-purple-500", "to-pink-400",
    "from-blue-600", "to-indigo-600",
    "from-pink-500", "to-red-500",
    // Shadows (Added these because modifiers like /60 need to be safelisted or used as full strings)
    {
      pattern: /(shadow)-(blue|cyan|emerald|purple|red|indigo)-(400|500|600)\/([0-9]+)/,
    },
  ],
  plugins: []
};