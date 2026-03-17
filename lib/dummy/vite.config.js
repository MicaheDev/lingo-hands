import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    // 1. Salir de 'maniqui_signer' y entrar en 'static/dist'
    outDir: "../../static/dist",
    emptyOutDir: true, // Limpia la carpeta antes de cada build
    rollupOptions: {
      output: {
        // Nombres fijos para que Jinja no pierda la referencia
        entryFileNames: `assets/[name].js`,
        chunkFileNames: `assets/[name].js`,
        assetFileNames: `assets/[name].[ext]`,
      },
    },
  },
});
