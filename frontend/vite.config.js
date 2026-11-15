import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// In dev, Vite serves the UI on :5173 and forwards /api to FastAPI on :8000,
// so the browser sees one origin and no CORS configuration is needed.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: { port: 5173 },
});
