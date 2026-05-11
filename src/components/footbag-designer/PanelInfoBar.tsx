import { useMemo } from "react";
import { getPanelShape } from "./designState.js";
import type { PanelColors } from "../../types.js";

const SHAPE_LABELS: Record<string, string> = {
  triangle: "Triangle",
  square: "Square",
  pentagon: "Pentagon",
  hexagon: "Hexagon",
  hexagon_large: "Large Hexagon",
};

interface PanelInfoBarProps {
  panelId: string | null;
  panelColors: PanelColors;
  allPanelIds: string[];
  lightBg: boolean;
  textureEnabled: boolean;
  onToggleBg: () => void;
  onToggleTexture: () => void;
  onApplyColor: () => void;
  onResetPanel: () => void;
  onCopyColor: () => void;
  onColorAllShape: () => void;
}

export function PanelInfoBar({
  panelId,
  panelColors,
  allPanelIds,
  lightBg,
  textureEnabled,
  onToggleBg,
  onToggleTexture,
  onApplyColor,
  onResetPanel,
  onCopyColor,
  onColorAllShape,
}: PanelInfoBarProps) {
  const shape = panelId ? getPanelShape(panelId) : null;
  const shapeLabel = shape ? (SHAPE_LABELS[shape] ?? shape) : null;
  const panelColor = panelId ? panelColors[panelId] : undefined;

  const shapePanelCount = useMemo(
    () => (shape ? allPanelIds.filter((id) => getPanelShape(id) === shape).length : 0),
    [shape, allPanelIds]
  );

  return (
    <div style={styles.bar}>
      <div style={styles.info}>
        {panelId ? (
          <>
            <span style={styles.panelId}>{panelId}</span>
            <span style={styles.sep}>·</span>
            <span style={styles.shapeLabel}>{shapeLabel}</span>
            <span style={styles.sep}>·</span>
            <span
              style={{
                ...styles.chip,
                background: panelColor ?? "#888888",
                opacity: panelColor ? 1 : 0.35,
              }}
            />
            <span style={styles.colorVal}>{panelColor ?? "default"}</span>
          </>
        ) : (
          <span style={styles.hint}>Click a panel to select it</span>
        )}
      </div>

      {panelId && (
        <div style={styles.actions}>
          <BarBtn onClick={onApplyColor}>Apply Color</BarBtn>
          <BarBtn onClick={onCopyColor} disabled={!panelColor}>Copy Color</BarBtn>
          <BarBtn onClick={onResetPanel} disabled={!panelColor}>Reset</BarBtn>
          {shapePanelCount > 1 && (
            <BarBtn onClick={onColorAllShape}>
              Paint all {shapeLabel}s ({shapePanelCount})
            </BarBtn>
          )}
        </div>
      )}

      <div style={styles.right}>
        <TextureToggle enabled={textureEnabled} onToggle={onToggleTexture} />
        <BgToggle light={lightBg} onToggle={onToggleBg} />
      </div>
    </div>
  );
}

function BarBtn({
  onClick,
  disabled,
  children,
}: {
  onClick: () => void;
  disabled?: boolean;
  children: React.ReactNode;
}) {
  return (
    <button
      style={{ ...styles.barBtn, opacity: disabled ? 0.4 : 1 }}
      onClick={onClick}
      disabled={disabled}
    >
      {children}
    </button>
  );
}

function BumpSphereIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="9" />
      <path d="M5 13 Q7 9 10 13 Q13 17 16 13 Q18 10 19 13" />
    </svg>
  );
}

function TextureToggle({ enabled, onToggle }: { enabled: boolean; onToggle: () => void }) {
  return (
    <button
      style={{ ...styles.togglePill, opacity: enabled ? 1 : 0.45, gap: "5px" }}
      onClick={onToggle}
      title={enabled ? "Disable suede texture" : "Enable suede texture"}
      aria-label={enabled ? "Disable suede texture" : "Enable suede texture"}
    >
      <BumpSphereIcon />
      <span style={{ fontSize: "11px", fontWeight: 600, letterSpacing: "0.04em" }}>Suede</span>
    </button>
  );
}

function SunIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <circle cx="12" cy="12" r="4" />
      <line x1="12" y1="2" x2="12" y2="5" />
      <line x1="12" y1="19" x2="12" y2="22" />
      <line x1="2" y1="12" x2="5" y2="12" />
      <line x1="19" y1="12" x2="22" y2="12" />
      <line x1="4.93" y1="4.93" x2="7.05" y2="7.05" />
      <line x1="16.95" y1="16.95" x2="19.07" y2="19.07" />
      <line x1="4.93" y1="19.07" x2="7.05" y2="16.95" />
      <line x1="16.95" y1="7.05" x2="19.07" y2="4.93" />
    </svg>
  );
}

function MoonIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
    </svg>
  );
}

function BgToggle({ light, onToggle }: { light: boolean; onToggle: () => void }) {
  return (
    <button
      style={styles.togglePill}
      onClick={onToggle}
      title={light ? "Switch to dark background" : "Switch to light background"}
      aria-label={light ? "Switch to dark background" : "Switch to light background"}
    >
      <span style={{ ...styles.toggleIcon, opacity: light ? 1 : 0.4, color: light ? "#ffd700" : "#ffffff" }}>
        <SunIcon />
      </span>
      <span style={{ ...styles.toggleKnob, transform: light ? "translateX(22px)" : "translateX(0)" }} />
      <span style={{ ...styles.toggleIcon, opacity: light ? 0.4 : 1, color: "#ffffff" }}>
        <MoonIcon />
      </span>
    </button>
  );
}

const styles = {
  bar: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    zIndex: 10,
    display: "flex",
    alignItems: "center",
    gap: "12px",
    padding: "0 14px",
    height: "46px",
    background: "rgba(10, 12, 18, 0.82)",
    borderBottom: "1px solid rgba(255,255,255,0.07)",
    backdropFilter: "blur(8px)",
  },
  info: {
    display: "flex",
    alignItems: "center",
    gap: "7px",
    flex: 1,
    minWidth: 0,
    overflow: "hidden",
  },
  panelId: {
    fontSize: "12px",
    fontFamily: "monospace",
    color: "var(--text)",
    letterSpacing: "0.03em",
    whiteSpace: "nowrap",
  },
  sep: {
    fontSize: "12px",
    color: "var(--muted)",
    flexShrink: 0,
  },
  shapeLabel: {
    fontSize: "12px",
    color: "var(--muted)",
    whiteSpace: "nowrap",
  },
  chip: {
    flexShrink: 0,
    width: "12px",
    height: "12px",
    borderRadius: "2px",
    border: "1px solid rgba(255,255,255,0.15)",
    display: "inline-block",
  },
  colorVal: {
    fontSize: "12px",
    fontFamily: "monospace",
    color: "var(--text)",
    letterSpacing: "0.03em",
    whiteSpace: "nowrap",
  },
  hint: {
    fontSize: "12px",
    color: "var(--muted)",
    fontStyle: "italic",
  },
  actions: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    flexShrink: 0,
  },
  barBtn: {
    padding: "4px 10px",
    background: "rgba(255,255,255,0.08)",
    border: "1px solid rgba(255,255,255,0.12)",
    borderRadius: "5px",
    color: "#ffffff",
    fontSize: "12px",
    fontWeight: 500,
    cursor: "pointer",
    whiteSpace: "nowrap",
    transition: "background-color 0.15s",
  },
  right: {
    flexShrink: 0,
    marginLeft: "4px",
    display: "flex",
    alignItems: "center",
    gap: "6px",
  },
  togglePill: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    padding: "4px 7px",
    background: "rgba(255,255,255,0.07)",
    border: "1px solid rgba(255,255,255,0.12)",
    borderRadius: "999px",
    cursor: "pointer",
    color: "#ffffff",
  },
  toggleIcon: {
    display: "flex",
    alignItems: "center",
    transition: "opacity 0.2s, color 0.2s",
    lineHeight: 0,
  },
  toggleKnob: {
    width: "14px",
    height: "14px",
    borderRadius: "50%",
    background: "#ffffff",
    flexShrink: 0,
    transition: "transform 0.2s",
    boxShadow: "0 1px 3px rgba(0,0,0,0.4)",
  },
} satisfies Record<string, React.CSSProperties>;
