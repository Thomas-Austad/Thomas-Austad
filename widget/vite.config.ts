import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

const rootDir = dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  plugins: [react()],
  build: {
    lib: {
      entry: resolve(rootDir, "src/main.tsx"),
      formats: ["es"],
      fileName: () => "talent-advisor-widget.js"
    },
    cssCodeSplit: false,
    rollupOptions: {
      output: {
        assetFileNames: "talent-advisor-widget.[ext]"
      }
    }
  },
  test: {
    environment: "jsdom",
    globals: true,
    include: ["tests/**/*.test.ts?(x)"],
    setupFiles: ["tests/setup.ts"]
  }
});
