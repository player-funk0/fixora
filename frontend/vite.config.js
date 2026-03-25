import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      // Proxies /api/* to Django during development — no CORS issues
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
