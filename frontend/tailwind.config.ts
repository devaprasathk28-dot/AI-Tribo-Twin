import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#172a36",
        muted: "#687985",
        paper: "#f4f6f5",
        line: "#e2e8e6",
        accent: "#187b68",
        warning: "#b96618",
        navy: {
          950: "#08111b",
          900: "#0c1928",
          850: "#102237",
          800: "#162e4a",
          750: "#1d3a5e",
          700: "#264872",
        },
      },
      boxShadow: {
        panel: "0 12px 30px rgba(23, 42, 54, 0.055)",
        card: "0 2px 8px rgba(12, 25, 40, 0.04), 0 1px 2px rgba(12, 25, 40, 0.02)",
        drawer: "0 20px 40px rgba(8, 17, 27, 0.4)",
      },
    },
  },
  plugins: [],
};

export default config;

