import { defineConfig } from "tsup";

export default defineConfig({
  entry: ["src/index.ts"],
  format: ["cjs", "esm"],
  dts: true,
  splitting: false,
  sourcemap: true,
  clean: true,
  globalName: "Gabber",
  target: 'esnext',
  external: ["axios", "livekit-client"],
  treeshake: true,
});