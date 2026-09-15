/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./templates/**/*.html", "./businessos/**/*.py"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "-apple-system", "BlinkMacSystemFont", '"Segoe UI"', "sans-serif"],
      },
      boxShadow: {
        panel: "0 1px 2px rgb(15 23 42 / 0.04), 0 8px 24px rgb(15 23 42 / 0.04)",
      },
    },
  },
  plugins: [],
};
