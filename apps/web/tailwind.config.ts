import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        neural: {
          bg: "#0a0a0f",
          surface: "#12121a",
          border: "#1e1e2e",
          accent: "#00d4ff",
          glow: "#00d4ff",
          success: "#00ff88",
          warning: "#ffaa00",
          error: "#ff4466",
          muted: "#6b7280",
        },
      },
      boxShadow: {
        glow: "0 0 10px rgba(0, 212, 255, 0.3), 0 0 20px rgba(0, 212, 255, 0.1)",
        "glow-sm": "0 0 5px rgba(0, 212, 255, 0.2)",
      },
      animation: {
        pulse_glow: "pulse_glow 2s ease-in-out infinite",
      },
      keyframes: {
        pulse_glow: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.6" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
