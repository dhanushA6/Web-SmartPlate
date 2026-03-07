/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f3f6ff',
          100: '#e1e9ff',
          200: '#c3d2ff',
          500: '#2457ff',
          600: '#1b43c4'
        }
      }
    }
  },
  plugins: []
};

