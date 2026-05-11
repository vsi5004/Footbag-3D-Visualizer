export type ModelType = "8" | "12" | "14" | "cubocta" | "18" | "26" | "32" | "38" | "42" | "62" | "92" | "122";

export type PanelColors = Record<string, string>;

export interface Design {
  version: 1;
  modelType: string;
  panelColors: PanelColors;
}

export interface ModelConfig {
  id: string;
  label: string;
  modelPath: string;
  metadataPath: string | null;
  available: boolean;
  description: string;
}

export interface PaletteEntry {
  id: string;
  label: string;
  color: string;
}
