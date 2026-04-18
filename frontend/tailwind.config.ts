import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Aviation navy + amber accent — mirrors the HTML prototype.
        meridian: {
          50: "#f5f7fa",
          100: "#e4e9f1",
          500: "#3b5e8c",
          700: "#21365a",
          900: "#0f1e38",
        },
        accent: {
          400: "#ffb74d",
          500: "#f59e0b",
        },
      },
      fontFamily: {
        sans: ["ui-sans-serif", "system-ui", "-apple-system", "Segoe UI", "Roboto", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
