import type { Design, PanelColors } from "../../types.js";

// Shape is encoded in panel IDs: "panel_001_pentagon" → "pentagon"
// "panel_001_hexagon_large" → "hexagon_large" (join all parts after index)
export function getPanelShape(panelId: string): string {
  const parts = panelId.split("_");
  return parts.slice(2).join("_");
}

export function applyColor(panelColors: PanelColors, panelId: string, color: string): PanelColors {
  return { ...panelColors, [panelId]: color };
}

export function resetPanel(panelColors: PanelColors, panelId: string): PanelColors {
  const next = { ...panelColors };
  delete next[panelId];
  return next;
}

export function resetAll(): PanelColors {
  return {};
}

export function applyShapeColor(
  panelColors: PanelColors,
  allPanelIds: string[],
  shape: string,
  color: string
): PanelColors {
  const next = { ...panelColors };
  for (const id of allPanelIds) {
    if (getPanelShape(id) === shape) {
      next[id] = color;
    }
  }
  return next;
}

export function applyColorToUnpainted(
  panelColors: PanelColors,
  allPanelIds: string[],
  color: string
): PanelColors {
  const next = { ...panelColors };
  for (const id of allPanelIds) {
    if (!next[id]) {
      next[id] = color;
    }
  }
  return next;
}

export function exportDesign(modelType: string, panelColors: PanelColors): Design {
  return { version: 1, modelType, panelColors };
}

export function importDesign(jsonString: string): Design {
  let data: unknown;
  try {
    data = JSON.parse(jsonString);
  } catch {
    throw new Error("Invalid JSON");
  }
  if (typeof data !== "object" || data === null) throw new Error("Invalid design format");

  const obj = data as Record<string, unknown>;

  if (obj.version !== 1) {
    throw new Error(`Unsupported design version: ${String(obj.version ?? "missing")}`);
  }
  if (!obj.modelType || typeof obj.modelType !== "string") {
    throw new Error("Missing or invalid modelType");
  }
  if (typeof obj.panelColors !== "object" || obj.panelColors === null) {
    throw new Error("Missing panelColors");
  }

  // Strip any non-panel-prefixed keys so unknown IDs are ignored gracefully
  const sanitizedColors: PanelColors = {};
  for (const [key, val] of Object.entries(obj.panelColors as Record<string, unknown>)) {
    if (key.startsWith("panel_") && typeof val === "string") {
      sanitizedColors[key] = val;
    }
  }

  return { version: 1, modelType: obj.modelType, panelColors: sanitizedColors };
}

// URL hash format: #v1:<base64-encoded-JSON>
// Using base64 keeps the URL compact and avoids percent-encoding noise.
export function encodeDesignToHash(design: Design): string {
  return "#v1:" + btoa(JSON.stringify(design));
}

export function decodeDesignFromHash(hash: string | null | undefined): Design {
  if (!hash || !hash.startsWith("#v1:")) {
    throw new Error("Not a valid design share link");
  }
  let json: string;
  try {
    json = atob(hash.slice(4)); // strip "#v1:"
  } catch {
    throw new Error("Invalid or corrupted share link");
  }
  return importDesign(json); // reuses all validation
}
