/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Palette PostalBI
        navy: {
          900: "#0A1628",
          800: "#0E1F3D",
          700: "#1E3A5F",
          600: "#2A4D7A",
        },
        postal: {
          DEFAULT: "#2E86AB",
          light: "#5BA3C0",
          dark: "#1A6485",
        },
        amber: {
          postal: "#F0A500",
          light: "#F7C44D",
          dark: "#C88400",
        },
        surface: {
          DEFAULT: "#F7F9FC",
          card: "#FFFFFF",
          muted: "#E8EDF4",
        },
      },
      fontFamily: {
        display: ["Space Grotesk", "sans-serif"],
        body: ["Inter", "sans-serif"],
      },
    },
  },
  plugins: [],
};
