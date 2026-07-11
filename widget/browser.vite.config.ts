import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const rootDir = dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  base: "/app/",
  plugins: [react()],
  build: {
    emptyOutDir: true,
    outDir: resolve(rootDir, "../browser_ui_dist"),
    rollupOptions: { input: resolve(rootDir, "browser.html") }
  }
});
