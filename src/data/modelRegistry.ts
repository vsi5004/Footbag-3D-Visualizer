import type { ModelConfig, ModelType } from "../types.js";

const base = import.meta.env.BASE_URL;

export const FOOTBAG_MODELS: Record<ModelType, ModelConfig> = {
  "8": {
    id: "8",
    label: "8 Panel",
    modelPath: `${base}models/footbag_8_panel.glb`,
    metadataPath: `${base}models/footbag_8_panel.json`,
    available: false,
    description: "Coming soon",
  },
  "12": {
    id: "12",
    label: "12 Panel",
    modelPath: `${base}models/footbag_12_panel.glb`,
    metadataPath: `${base}models/footbag_12_panel.json`,
    available: true,
    description: "12 pentagons",
  },
  "14": {
    id: "14",
    label: "14 Panel",
    modelPath: `${base}models/footbag_14_panel.glb`,
    metadataPath: `${base}models/footbag_14_panel.json`,
    available: true,
    description: "6 squares + 8 hexagons",
  },
  "cubocta": {
    id: "cubocta",
    label: "Cubocta",
    modelPath: `${base}models/footbag_cubocta_panel.glb`,
    metadataPath: `${base}models/footbag_cubocta_panel.json`,
    available: true,
    description: "6 squares + 8 triangles",
  },
  "18": {
    id: "18",
    label: "18 Panel",
    modelPath: `${base}models/footbag_18_panel.glb`,
    metadataPath: `${base}models/footbag_18_panel.json`,
    available: true,
    description: "6 squares + 12 hexagons",
  },
  "26": {
    id: "26",
    label: "26 Panel",
    modelPath: `${base}models/footbag_26_panel.glb`,
    metadataPath: `${base}models/footbag_26_panel.json`,
    available: true,
    description: "18 squares + 8 triangles",
  },
  "32": {
    id: "32",
    label: "32 Panel",
    modelPath: `${base}models/footbag_32_panel.glb`,
    metadataPath: `${base}models/footbag_32_panel.json`,
    available: true,
    description: "12 pentagons + 20 hexagons",
  },
  "38": {
    id: "38",
    label: "38 Panel",
    modelPath: `${base}models/footbag_38_panel.glb`,
    metadataPath: `${base}models/footbag_38_panel.json`,
    available: true,
    description: "6 squares + 24 hexagons + 8 large hexagons",
  },
  "42": {
    id: "42",
    label: "42 Panel",
    modelPath: `${base}models/footbag_42_panel.glb`,
    metadataPath: `${base}models/footbag_42_panel.json`,
    available: true,
    description: "12 pentagons + 30 hexagons",
  },
  "62": {
    id: "62",
    label: "62 Panel",
    modelPath: `${base}models/footbag_62_panel.glb`,
    metadataPath: `${base}models/footbag_62_panel.json`,
    available: true,
    description: "12 pentagons + 30 squares + 20 triangles",
  },
  "92": {
    id: "92",
    label: "92 Panel",
    modelPath: `${base}models/footbag_92_panel.glb`,
    metadataPath: `${base}models/footbag_92_panel.json`,
    available: true,
    description: "12 pentagons + 60 hexagons + 20 large hexagons",
  },
  "122": {
    id: "122",
    label: "122 Panel",
    modelPath: `${base}models/footbag_122_panel.glb`,
    metadataPath: `${base}models/footbag_122_panel.json`,
    available: true,
    description: "12 pentagons + 90 hexagons + 20 large hexagons",
  },
};

export const MODEL_ORDER: ModelType[] = ["8", "12", "14", "cubocta", "18", "26", "32", "38", "42", "62", "92", "122"];

export const DEFAULT_MODEL_TYPE: ModelType = "32";
