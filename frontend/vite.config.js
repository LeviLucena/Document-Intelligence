import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const api = "http://127.0.0.1:8000";

// Em produção o FastAPI serve o build em /static; em dev o Vite faz proxy da API.
export default defineConfig(({ command }) => ({
  base: command === "build" ? "/static/" : "/",
  plugins: [react()],
  build: { outDir: "../app/static", emptyOutDir: true },
  server: { proxy: { "/documents": api, "/ask": api, "/health": api, "/auth": api } },
}));
