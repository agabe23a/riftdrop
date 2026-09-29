/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bomet: {
          green: '#2E8B57', // Primary Action (Forest Green)
          blue: '#1E90FF',  // Secondary/Trust (River Blue)
          gold: '#FFC107',  // Accents/Highlights (Star Gold)
          gray: '#F3F4F6',  // Soft backgrounds
          dark: '#111827',  // Crisp text
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'], // Premium, readable font
      }
    },
  },
  plugins: [],
}