import path from "path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    allowedHosts: ['goliath'],
    port: 10804,
    strictPort: true,
    host: "127.0.0.1",
    proxy: {
      "/api/logs": {
        target: "http://127.0.0.1:11068",
        changeOrigin: true,
      },
    },
  }
});
