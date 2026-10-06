/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./templates/**/*.html", "./businessos/**/*.py"],
  theme: {
    extend: {
      colors: {
        brand: "var(--bos-accent)",
        "brand-soft": "var(--bos-accent-soft)",
        workspace: "var(--bos-workspace)",
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', "Inter", "ui-sans-serif", "system-ui", "-apple-system", "BlinkMacSystemFont", '"Segoe UI"', "sans-serif"],
      },
      boxShadow: {
        panel: "0 1px 3px rgb(15 23 42 / 0.08)",
      },
    },
  },
  plugins: [],
};
