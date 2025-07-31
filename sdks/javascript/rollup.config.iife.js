const typescript = require("@rollup/plugin-typescript");
const node_resolve = require("@rollup/plugin-node-resolve");

module.exports = {
  input: ["src/index.ts"],
  output: { dir: "dist", format: "iife", entryFileNames: "[name].iife.js", name: "Gabber" },
  plugins: [
    typescript({ tsconfig: "./tsconfig.json" }),
    node_resolve({ browser: true, preferBuiltins: false }),
  ],
};