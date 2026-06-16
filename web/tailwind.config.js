/** Design system: Data-Dense Dashboard (ui-ux-pro-max). */
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: { DEFAULT: "#2563EB", light: "#3B82F6" },
        accent: "#F97316",
        bg: "#F8FAFC",
        surface: "#FFFFFF",
        ink: "#1E293B",
        muted: "#64748B",
        line: "#E2E8F0",
        success: "#16A34A",
        warning: "#F59E0B",
        danger: "#DC2626",
      },
      fontFamily: {
        sans: ["'Fira Sans'", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["'Fira Code'", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};
