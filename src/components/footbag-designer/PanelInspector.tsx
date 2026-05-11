import { useMemo } from "react";
import { getPanelShape } from "./designState.js";
import type { PanelColors } from "../../types.js";

const SHAPE_LABELS: Record<string, string> = {
  pentagon: "Pentagon",
  hexagon: "Hexagon",
  hexagon_large: "Large Hexagon",
  square: "Square",
};

interface PanelInspectorProps {
  panelId: string | null;
  panelColors: PanelColors;
  allPanelIds: string[];
  onApplyColor: () => void;
  onResetPanel: () => void;
  onCopyColor: () => void;
  onColorAllShape: () => void;
}

export function PanelInspector({
  panelId,
  panelColors,
  allPanelIds,
  onApplyColor,
  onResetPanel,
  onCopyColor,
  onColorAllShape,
}: PanelInspectorProps) {
  const shape = panelId ? getPanelShape(panelId) : null;
  const shapeLabel = shape ? (SHAPE_LABELS[shape] ?? shape) : null;
  const panelColor = panelId ? panelColors[panelId] : undefined;

  const shapePanelCount = useMemo(
    () => (shape ? allPanelIds.filter((id) => getPanelShape(id) === shape).length : 0),
    [shape, allPanelIds]
  );

  if (!panelId) {
    return <p style={styles.empty}>Click a panel on the model to select it.</p>;
  }

  return (
    <div style={styles.root}>
      <div style={styles.infoBlock}>
        <InfoRow label="ID" value={panelId} mono />
        <InfoRow label="Shape" value={shapeLabel ?? ""} />
        <div style={styles.infoRow}>
          <span style={styles.key}>Color</span>
          <span style={styles.colorValue}>
            <span
              style={{
                ...styles.chip,
                background: panelColor ?? "#888888",
                opacity: panelColor ? 1 : 0.4,
              }}
            />
            <span style={styles.val}>{panelColor ?? "default"}</span>
          </span>
        </div>
      </div>

      <div style={styles.actions}>
        <button style={styles.btnPrimary} onClick={onApplyColor}>
          Apply Color
        </button>
        <button
          style={{ ...styles.btn, opacity: panelColor ? 1 : 0.45 }}
          onClick={onCopyColor}
          disabled={!panelColor}
        >
          Copy Color from Panel
        </button>
        <button
          style={{ ...styles.btn, opacity: panelColor ? 1 : 0.45 }}
          onClick={onResetPanel}
          disabled={!panelColor}
        >
          Reset This Panel
        </button>
        {shapePanelCount > 1 && (
          <button style={styles.btn} onClick={onColorAllShape}>
            Color All {shapeLabel}s&nbsp;({shapePanelCount})
          </button>
        )}
      </div>
    </div>
  );
}

function InfoRow({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div style={styles.infoRow}>
      <span style={styles.key}>{label}</span>
      <span style={{ ...styles.val, fontFamily: mono ? "monospace" : "inherit" }}>
        {value}
      </span>
    </div>
  );
}

const styles = {
  root: {
    display: "flex",
    flexDirection: "column",
    gap: "12px",
  },
  empty: {
    margin: 0,
    fontSize: "13px",
    color: "var(--muted)",
    fontStyle: "italic",
    lineHeight: 1.5,
  },
  infoBlock: {
    display: "flex",
    flexDirection: "column",
    gap: "8px",
    padding: "10px 12px",
    background: "#10131a",
    borderRadius: "8px",
    border: "1px solid var(--card-btn)",
  },
  infoRow: {
    display: "flex",
    flexDirection: "column",
    gap: "2px",
  },
  colorValue: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
  },
  chip: {
    display: "inline-block",
    width: "14px",
    height: "14px",
    borderRadius: "3px",
    border: "1px solid var(--hover)",
    flexShrink: 0,
  },
  key: {
    fontSize: "11px",
    color: "var(--muted)",
    textTransform: "uppercase",
    letterSpacing: "0.06em",
  },
  val: {
    fontSize: "13px",
    color: "var(--text)",
    wordBreak: "break-all",
  },
  actions: {
    display: "flex",
    flexDirection: "column",
    gap: "6px",
  },
  btnPrimary: {
    padding: "8px 12px",
    background: "var(--accent)",
    border: "none",
    borderRadius: "6px",
    color: "#001a33",
    fontSize: "13px",
    fontWeight: 600,
    cursor: "pointer",
    textAlign: "left",
    transition: "filter 0.2s",
  },
  btn: {
    padding: "7px 12px",
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
} satisfies Record<string, React.CSSProperties>;
