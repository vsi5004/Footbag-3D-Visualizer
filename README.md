# Footbag 3D Designer

[![Deploy](https://github.com/vsi5004/Footbag-3D-Visualizer/actions/workflows/deploy.yml/badge.svg)](https://github.com/vsi5004/Footbag-3D-Visualizer/actions/workflows/deploy.yml)
[![Release](https://img.shields.io/github/v/release/vsi5004/Footbag-3D-Visualizer)](https://github.com/vsi5004/Footbag-3D-Visualizer/releases/latest)
[![Node](https://img.shields.io/badge/node-%3E%3D18-brightgreen)](https://nodejs.org)

An interactive browser tool for designing color patterns on 3D footbag models. Paint individual panels, save your design as a JSON file, and share it with a single URL — no account or backend required.

## What it does

- **3D model viewer** — Rotate and inspect the footbag from any angle using mouse or touch.
- **Click-to-paint** — Click any panel on the model to paint it with the active color.
- **Color palette** — 21 fabric-appropriate preset colors plus a custom color picker.
- **Shape tools** — Paint all panels of the same shape in one click. Fill all unpainted panels at once.
- **Color summary** — Live breakdown of painted panels by shape and color.
- **Suede texture** — Toggle a procedural suede normal map on/off for a realistic fabric look.
- **Background toggle** — Switch the canvas between dark and light backgrounds.
- **Multiple models** — Switch between 11 footbag designs ranging from 12 to 122 panels.
- **Export / Import** — Save your design as a JSON file and reload it later on any machine.
- **Shareable link** — Click "Share Link" to encode the full design into the URL. Send it to anyone; they open the link and see exactly your design.
- **URL persistence** — The URL hash updates automatically when you share or import, so the browser back button and bookmarks reflect your design state.

## Models

| ID | Panels | Shapes |
|----|--------|--------|
| 12 | 12 | 12 pentagons |
| 14 | 14 | 6 squares + 8 hexagons |
| cubocta | 14 | 6 squares + 8 triangles |
| 18 | 18 | 6 squares + 12 hexagons |
| 26 | 26 | 18 squares + 8 triangles |
| 32 | 32 | 12 pentagons + 20 hexagons |
| 38 | 38 | 6 squares + 24 hexagons + 8 large hexagons |
| 42 | 42 | 12 pentagons + 30 hexagons |
| 62 | 62 | 12 pentagons + 30 squares + 20 triangles |
| 92 | 92 | 12 pentagons + 60 hexagons + 20 large hexagons |
| 122 | 122 | 12 pentagons + 90 hexagons + 20 large hexagons |

## Dev environment setup

**Prerequisites:** Node.js 18+, npm

```bash
# Install dependencies
npm install

# Start the dev server (hot-reload)
npm run dev
# → http://localhost:4321

# Run unit tests
npm test

# Production build (outputs to dist/)
npm run build
```

## Deploying to GitHub Pages

Set two repository variables in **Settings → Variables → Actions**:

| Variable | Example value |
|----------|---------------|
| `SITE`   | `https://your-username.github.io` |
| `BASE`   | `/Footbag-3D-Visualizer` |

The included GitHub Actions workflow (`.github/workflows/deploy.yml`) runs tests, builds, and publishes automatically on every push to `main`.

## Versioning

The app version is read from `package.json` at build time and displayed in the sidebar. To cut a release:

```bash
npm version patch   # or minor / major
git push --follow-tags
```

This bumps `package.json`, creates a `vX.Y.Z` git tag, and triggers a new deployment.

## Embedding in another page

Once deployed, the tool can be embedded as an iframe:

```html
<iframe
  src="https://your-username.github.io/Footbag-3D-Visualizer/"
  width="100%"
  height="700"
  style="border: none;"
></iframe>
```

Shareable design links (`#v1:...` hash) work inside iframes too — the design is encoded entirely in the URL, so no cross-origin communication is needed.

## Generating models

The `footbag_panel_generator.py` Blender script generates GLB model files. Run it from Blender's Scripting workspace (`Alt+P`). Set `BAG_STYLE` at the top of the script to the desired panel count, then copy the exported GLB (and JSON if generated) into `public/models/`.

## Tech stack

- [Astro](https://astro.build) — static site generator, zero JS by default
- [React Three Fiber](https://github.com/pmndrs/react-three-fiber) — declarative Three.js renderer
- [Three.js](https://threejs.org) — 3D engine (GLB model loading, per-panel material cloning, normal/roughness maps)
- [Vitest](https://vitest.dev) — unit tests for state logic
- TypeScript throughout

## Share link format

Design links use the format `#v1:<base64(JSON)>`. The hash is never sent to any server — it lives entirely in the browser. The encoded JSON looks like:

```json
{
  "version": 1,
  "modelType": "32",
  "panelColors": {
    "panel_001_pentagon": "#c41e3a",
    "panel_013_hexagon": "#2040a0"
  }
}
```
