import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

// Build the SPA into backend/static so FastAPI serves API + UI from one container.
export default defineConfig({
  plugins: [react()],
  resolve: { alias: { "@": path.resolve(__dirname, "src") } },
  build: { outDir: "../backend/static", emptyOutDir: true },
  server: { proxy: { "/translate": "http://127.0.0.1:8080", "/terms": "http://127.0.0.1:8080", "/review": "http://127.0.0.1:8080", "/corrections": "http://127.0.0.1:8080", "/metrics": "http://127.0.0.1:8080", "/profiles": "http://127.0.0.1:8080", "/health": "http://127.0.0.1:8080" } },
});
