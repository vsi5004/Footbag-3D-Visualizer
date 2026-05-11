import { defineConfig } from "astro/config";
import react from "@astrojs/react";
import { readFileSync } from "fs";

const { version } = JSON.parse(readFileSync("./package.json", "utf8"));

// For GitHub Pages deployment, set these environment variables:
//   SITE=https://yourname.github.io
//   BASE=/Footbag-3D-Visualizer
// For a custom domain set BASE=/ and SITE=https://yourdomain.com
const site = process.env.SITE || undefined;
const base = (process.env.BASE || "/").replace(/\/?$/, "/");

export default defineConfig({
  output: "static",
  site,
  base,
  integrations: [react()],
  vite: {
    define: {
      __APP_VERSION__: JSON.stringify(version),
    },
    build: {
      // Three.js + R3F together are ~900KB minified / ~250KB gzipped. This is
      // normal for a WebGL app — raise the warning threshold to avoid noise.
      chunkSizeWarningLimit: 1000,
    },
  },
});
