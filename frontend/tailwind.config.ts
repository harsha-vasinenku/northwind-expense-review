import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        compliant: {
          bg: "#dcfce7",
          text: "#15803d",
          border: "#86efac",
        },
        flagged: {
          bg: "#fee2e2",
          text: "#b91c1c",
          border: "#fca5a5",
        },
        review: {
          bg: "#fef9c3",
          text: "#a16207",
          border: "#fde047",
        },
      },
    },
  },
  plugins: [],
};

export default config;
