/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0fdf4',
          100: '#dcfce7',
          200: '#bbf7d0',
          500: '#22C55E',
          600: '#16A34A'
        },
        nutrition: {
          primary: '#22C55E',
          secondary: '#16A34A',
          accent: '#F59E0B',
          carbs: '#F97316',
          protein: '#3B82F6',
          fat: '#A855F7',
          fiber: '#22C55E'
        }
      },
      boxShadow: {
        'card': '0 1px 3px 0 rgb(0 0 0 / 0.05), 0 1px 2px -1px rgb(0 0 0 / 0.05)',
        'card-hover': '0 4px 6px -1px rgb(0 0 0 / 0.07), 0 2px 4px -2px rgb(0 0 0 / 0.07)'
      }
    }
  },
  plugins: []
};

