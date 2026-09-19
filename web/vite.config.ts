import { defineConfig } from "vitest/config";

export default defineConfig({
  server: {
    host: "127.0.0.1",
    port: 5174,
  },
  preview: {
    host: "127.0.0.1",
    port: 4174,
  },
  test: {
    include: ["src/**/*.test.ts"],
  },
});
