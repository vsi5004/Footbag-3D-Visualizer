import { useState, useCallback, useRef, useEffect, type ReactNode } from "react";

const SKIP_MODEL_WARNING_KEY = "footbag.skipModelWarning";
import { FOOTBAG_MODELS, DEFAULT_MODEL_TYPE } from "../../data/modelRegistry.js";
import { DEFAULT_PALETTE } from "../../data/defaultPalettes.js";
import {
  applyColor,
  resetPanel,
  resetAll,
  applyShapeColor,
  applyColorToUnpainted,
  getPanelShape,
  exportDesign,
  importDesign,
  encodeDesignToHash,
  decodeDesignFromHash,
} from "./designState.js";
import { FootbagCanvas } from "./FootbagCanvas.jsx";
import { ModelSelector } from "./ModelSelector.jsx";
import { ColorPalette } from "./ColorPalette.jsx";
import { PanelInfoBar } from "./PanelInfoBar.jsx";
import { ColorSummary } from "./ColorSummary.jsx";
import type { Design, ModelType, PanelColors } from "../../types.js";

interface StatusMessage {
  text: string;
  isError: boolean;
}

export function FootbagDesigner() {
  const [modelType, setModelType] = useState<ModelType>(DEFAULT_MODEL_TYPE);
  const [selectedPanelId, setSelectedPanelId] = useState<string | null>(null);
  const [selectedColor, setSelectedColor] = useState<string>(DEFAULT_PALETTE[0].color);
  const [panelColors, setPanelColors] = useState<PanelColors>({});
  const [allPanelIds, setAllPanelIds] = useState<string[]>([]);
  const [statusMessage, setStatusMessage] = useState<StatusMessage | null>(null);
  const [shareFeedback, setShareFeedback] = useState(false);
  const [lightBg, setLightBg] = useState(false);
  const [textureEnabled, setTextureEnabled] = useState(true);
  const [pendingModelType, setPendingModelType] = useState<ModelType | null>(null);
  const importInputRef = useRef<HTMLInputElement>(null);
  const statusTimerRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  // Ref so handlePanelSelect can read the current color without it as a dep
  const selectedColorRef = useRef(selectedColor);
  selectedColorRef.current = selectedColor;

  const showStatus = useCallback((text: string, isError = false) => {
    clearTimeout(statusTimerRef.current);
    setStatusMessage({ text, isError });
    statusTimerRef.current = setTimeout(() => setStatusMessage(null), 4000);
  }, []);

  // Apply a validated design object to component state
  const applyDesign = useCallback((design: Design) => {
    if (!FOOTBAG_MODELS[design.modelType as ModelType]?.available) {
      throw new Error(`Model "${design.modelType}-panel" is not available in this version`);
    }
    setModelType(design.modelType as ModelType);
    setPanelColors(design.panelColors);
    setSelectedPanelId(null);
    setAllPanelIds([]);
  }, []);

  // On mount, auto-load a design encoded in the URL hash
  useEffect(() => {
    const { hash } = window.location;
    if (!hash.startsWith("#v1:")) return;
    try {
      const design = decodeDesignFromHash(hash);
      applyDesign(design);
    } catch (err) {
      showStatus(err instanceof Error ? err.message : String(err), true);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const model = FOOTBAG_MODELS[modelType];

  const applyModelChange = useCallback((newType: ModelType) => {
    setModelType(newType);
    setSelectedPanelId(null);
    setPanelColors({});
    setAllPanelIds([]);
    history.replaceState(null, "", window.location.pathname + window.location.search);
  }, []);

  const handleModelChange = useCallback((newType: ModelType) => {
    if (newType === modelType) return;
    const hasDesign = Object.keys(panelColors).length > 0;
    const skipWarning = localStorage.getItem(SKIP_MODEL_WARNING_KEY) === "true";
    if (!hasDesign || skipWarning) {
      applyModelChange(newType);
    } else {
      setPendingModelType(newType);
    }
  }, [modelType, panelColors, applyModelChange]);

  const handleConfirmModelChange = useCallback((skipNext: boolean) => {
    if (skipNext) localStorage.setItem(SKIP_MODEL_WARNING_KEY, "true");
    if (pendingModelType) applyModelChange(pendingModelType);
    setPendingModelType(null);
  }, [pendingModelType, applyModelChange]);

  const handleCancelModelChange = useCallback(() => {
    setPendingModelType(null);
  }, []);

  const handlePanelSelect = useCallback((panelId: string) => {
    setSelectedPanelId(panelId);
    setPanelColors((prev) => applyColor(prev, panelId, selectedColorRef.current));
  }, []); // stable — reads selectedColor via ref at call time

  const handlePanelsDiscovered = useCallback((panels: string[]) => {
    setAllPanelIds(panels);
  }, []);

  const handleApplyColor = useCallback(() => {
    if (!selectedPanelId) return;
    setPanelColors((prev) => applyColor(prev, selectedPanelId, selectedColor));
  }, [selectedPanelId, selectedColor]);

  const handleResetPanel = useCallback(() => {
    if (!selectedPanelId) return;
    setPanelColors((prev) => resetPanel(prev, selectedPanelId));
  }, [selectedPanelId]);

  const handleCopyColor = useCallback(() => {
    if (selectedPanelId && panelColors[selectedPanelId]) {
      setSelectedColor(panelColors[selectedPanelId]);
    }
  }, [selectedPanelId, panelColors]);

  const handleColorAllShape = useCallback(() => {
    if (!selectedPanelId) return;
    const shape = getPanelShape(selectedPanelId);
    setPanelColors((prev) => applyShapeColor(prev, allPanelIds, shape, selectedColor));
  }, [selectedPanelId, allPanelIds, selectedColor]);

  const handleColorUnpainted = useCallback(() => {
    setPanelColors((prev) => applyColorToUnpainted(prev, allPanelIds, selectedColor));
  }, [allPanelIds, selectedColor]);

  const handleDeselect = useCallback(() => {
    setSelectedPanelId(null);
  }, []);

  const handleResetAll = useCallback(() => {
    setPanelColors(resetAll());
    setSelectedPanelId(null);
  }, []);

  const handleExport = useCallback(() => {
    const design = exportDesign(modelType, panelColors);
    const blob = new Blob([JSON.stringify(design, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `footbag-design-${modelType}panel.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [modelType, panelColors]);

  const handleShare = useCallback(async () => {
    const design = exportDesign(modelType, panelColors);
    const hash = encodeDesignToHash(design);
    // Update the URL hash so the current tab also reflects the shared state
    history.replaceState(null, "", hash);
    const shareUrl = window.location.href;
    try {
      await navigator.clipboard.writeText(shareUrl);
      setShareFeedback(true);
      setTimeout(() => setShareFeedback(false), 2000);
    } catch {
      // Clipboard API unavailable (e.g. non-HTTPS dev) — show URL in status
      showStatus("Share URL set in address bar — copy it manually", false);
    }
  }, [modelType, panelColors, showStatus]);

  const handleImportClick = useCallback(() => {
    importInputRef.current?.click();
  }, []);

  const handleImportFile = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;
      e.target.value = "";

      const reader = new FileReader();
      reader.onerror = () => showStatus("Could not read file", true);
      reader.onload = (ev) => {
        try {
          const result = ev.target?.result;
          if (typeof result !== "string") return;
          const design = importDesign(result);
          applyDesign(design);
          // Reflect imported design in URL hash so the user can share it
          history.replaceState(null, "", encodeDesignToHash(design));
        } catch (err) {
          showStatus(err instanceof Error ? err.message : String(err), true);
        }
      };
      reader.readAsText(file);
    },
    [applyDesign, showStatus]
  );

  return (
    <div className="fd-root" style={styles.root}>
      {/* Full-width header */}
      <header style={styles.header}>
        <span style={styles.logo}>Footbag Designer</span>
        <div style={styles.headerActions}>
          {statusMessage && (
            <span style={{ ...styles.status, color: statusMessage.isError ? "#ff8888" : "#4ade80" }}>
              {statusMessage.text}
            </span>
          )}
          <button style={styles.headerBtn} onClick={handleImportClick}>
            Import
          </button>
          <button style={styles.headerBtn} onClick={handleExport}>
            Export
          </button>
          <button
            style={{ ...styles.headerBtn, ...styles.headerBtnPrimary }}
            onClick={handleShare}
          >
            {shareFeedback ? "✓ Copied!" : "Share Link"}
          </button>
          <input
            ref={importInputRef}
            type="file"
            accept=".json"
            style={{ display: "none" }}
            onChange={handleImportFile}
            aria-label="Import design JSON"
          />
        </div>
      </header>

      {/* Two-column body */}
      <div style={styles.body}>
        {/* Controls sidebar */}
        <aside className="fd-controls" style={styles.controls}>
          <Section title="Panel Count">
            <ModelSelector
              models={FOOTBAG_MODELS}
              currentType={modelType}
              onSelect={handleModelChange}
            />
          </Section>

          <Section title="Color">
            <ColorPalette
              palette={DEFAULT_PALETTE}
              selectedColor={selectedColor}
              onColorSelect={setSelectedColor}
            />
          </Section>

          <Section title="Color Summary">
            <ColorSummary
              panelColors={panelColors}
              allPanelIds={allPanelIds}
              onColorSelect={setSelectedColor}
            />
          </Section>

          <Section title="Actions">
            <div style={styles.actionButtons}>
              <button style={styles.actionBtn} onClick={handleColorUnpainted}>
                Fill Unpainted Panels
              </button>
              <button
                style={{ ...styles.actionBtn, color: "#ff8888" }}
                onClick={handleResetAll}
              >
                Reset All Panels
              </button>
            </div>
          </Section>

          <div style={styles.versionTag}>v{__APP_VERSION__}</div>
        </aside>

        {/* 3D canvas */}
        <main className="fd-canvas-area" style={styles.canvasArea}>
          <PanelInfoBar
            panelId={selectedPanelId}
            panelColors={panelColors}
            allPanelIds={allPanelIds}
            lightBg={lightBg}
            textureEnabled={textureEnabled}
            onToggleBg={() => setLightBg((v) => !v)}
            onToggleTexture={() => setTextureEnabled((v) => !v)}
            onApplyColor={handleApplyColor}
            onResetPanel={handleResetPanel}
            onCopyColor={handleCopyColor}
            onColorAllShape={handleColorAllShape}
          />
          <FootbagCanvas
            modelPath={model.modelPath}
            panelColors={panelColors}
            selectedPanelId={selectedPanelId}
            bgColor={lightBg ? "#d8d8d8" : "#0e0f12"}
            textureEnabled={textureEnabled}
            onPanelSelect={handlePanelSelect}
            onPanelsDiscovered={handlePanelsDiscovered}
            onDeselect={handleDeselect}
          />
        </main>
      </div>

      {pendingModelType && (
        <ModelChangeDialog
          pendingLabel={FOOTBAG_MODELS[pendingModelType].label}
          onConfirm={handleConfirmModelChange}
          onCancel={handleCancelModelChange}
        />
      )}
    </div>
  );
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div style={sectionStyles.root}>
      <div style={sectionStyles.header}>
        <h3 style={sectionStyles.title}>{title}</h3>
      </div>
      {children}
    </div>
  );
}

const sectionStyles = {
  root: { marginBottom: "20px" },
  header: {
    marginBottom: "14px",
    paddingBottom: "12px",
    borderBottom: "1px solid #364064",
  },
  title: { margin: 0, fontSize: "16px", fontWeight: 600, color: "var(--text)" },
} satisfies Record<string, React.CSSProperties>;

const styles = {
  root: {
    background: "var(--bg)",
    color: "var(--text)",
    fontFamily: "inherit",
  },
  header: {
    gridColumn: "1 / -1",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "14px 20px",
    background: "var(--card)",
    borderBottom: "1px solid var(--border)",
    flexShrink: 0,
  },
  logo: { fontSize: "16px", fontWeight: 700, color: "var(--text)", letterSpacing: "0.02em" },
  headerActions: { display: "flex", alignItems: "center", gap: "10px" },
  status: { fontSize: "12px", maxWidth: "260px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" },
  headerBtn: {
    padding: "8px 16px",
    background: "var(--card-btn)",
    border: "1px solid var(--hover)",
    borderRadius: "6px",
    color: "var(--text)",
    fontSize: "14px",
    fontWeight: 600,
    cursor: "pointer",
    transition: "background-color 0.2s",
    whiteSpace: "nowrap",
  },
  headerBtnPrimary: {
    background: "var(--accent)",
    border: "none",
    color: "#001a33",
    minWidth: "100px",
  },
  body: { display: "contents" },
  controls: {
    background: "var(--card)",
    borderRight: "1px solid var(--border)",
    padding: "16px",
    overflowY: "auto",
    display: "flex",
    flexDirection: "column",
  },
  canvasArea: { minWidth: 0, minHeight: 0, position: "relative" },
  actionButtons: { display: "flex", flexDirection: "column", gap: "8px" },
  actionBtn: {
    padding: "8px 12px",
    background: "var(--card-btn)",
    border: "1px solid var(--hover)",
    borderRadius: "6px",
    color: "var(--text)",
    fontSize: "13px",
    fontWeight: 500,
    cursor: "pointer",
    textAlign: "left",
    transition: "background-color 0.2s",
  },
  versionTag: {
    marginTop: "auto",
    padding: "10px 14px",
    fontSize: "11px",
    color: "var(--muted)",
    letterSpacing: "0.04em",
  },
} satisfies Record<string, React.CSSProperties>;

function ModelChangeDialog({
  pendingLabel,
  onConfirm,
  onCancel,
}: {
  pendingLabel: string;
  onConfirm: (skipNext: boolean) => void;
  onCancel: () => void;
}) {
  const [skipNext, setSkipNext] = useState(false);

  return (
    <div style={dialogStyles.backdrop} onClick={onCancel}>
      <div style={dialogStyles.card} onClick={(e) => e.stopPropagation()}>
        <h4 style={dialogStyles.title}>Switch to {pendingLabel}?</h4>
        <p style={dialogStyles.body}>
          Switching models will clear your current design. This cannot be undone.
        </p>
        <label style={dialogStyles.checkLabel}>
          <input
            type="checkbox"
            checked={skipNext}
            onChange={(e) => setSkipNext(e.target.checked)}
            style={dialogStyles.checkbox}
          />
          Don't show this again
        </label>
        <div style={dialogStyles.actions}>
          <button style={dialogStyles.cancelBtn} onClick={onCancel}>
            Cancel
          </button>
          <button style={dialogStyles.confirmBtn} onClick={() => onConfirm(skipNext)}>
            Switch Model
          </button>
        </div>
      </div>
    </div>
  );
}

const dialogStyles = {
  backdrop: {
    position: "fixed",
    inset: 0,
    zIndex: 100,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    background: "rgba(0,0,0,0.6)",
    backdropFilter: "blur(3px)",
  },
  card: {
    background: "var(--card)",
    border: "1px solid var(--border)",
    borderRadius: "12px",
    padding: "24px",
    width: "340px",
    display: "flex",
    flexDirection: "column",
    gap: "14px",
    boxShadow: "0 20px 60px rgba(0,0,0,0.5)",
  },
  title: {
    margin: 0,
    fontSize: "16px",
    fontWeight: 700,
    color: "var(--text)",
  },
  body: {
    margin: 0,
    fontSize: "13px",
    color: "var(--muted)",
    lineHeight: 1.6,
  },
  checkLabel: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    fontSize: "13px",
    color: "var(--text)",
    cursor: "pointer",
  },
  checkbox: {
    width: "14px",
    height: "14px",
    accentColor: "var(--accent)",
    cursor: "pointer",
    flexShrink: 0,
  },
  actions: {
    display: "flex",
    justifyContent: "flex-end",
    gap: "8px",
    marginTop: "4px",
  },
  cancelBtn: {
    padding: "8px 16px",
    background: "var(--card-btn)",
    border: "1px solid var(--hover)",
    borderRadius: "6px",
    color: "var(--text)",
    fontSize: "13px",
    fontWeight: 500,
    cursor: "pointer",
  },
  confirmBtn: {
    padding: "8px 16px",
    background: "#c0392b",
    border: "none",
    borderRadius: "6px",
    color: "#ffffff",
    fontSize: "13px",
    fontWeight: 600,
    cursor: "pointer",
  },
} satisfies Record<string, React.CSSProperties>;
