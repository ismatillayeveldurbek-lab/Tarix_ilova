import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// `npm run dev` paytida /api so'rovlari Python serverga (8000-port) yo'naltiriladi
export default defineConfig({
  plugins: [react()],
  server: { proxy: { "/api": "http://localhost:8000" } },
});
