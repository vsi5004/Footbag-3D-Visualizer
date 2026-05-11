import { useMemo } from "react";
import { getPanelShape } from "./designState.js";
import type { PanelColors } from "../../types.js";

interface ColorSummaryProps {
  panelColors: PanelColors;
  allPanelIds: string[];
  onColorSelect: (color: string) => void;
}

const SHAPE_LABELS: Record<string, string> = {
  pentagon: "Pentagon",
  hexagon: "Hexagon",
  hexagon_large: "Large Hexagon",
  square: "Square",
};

type ColorCount = { color: string; count: number };
type ShapeGroup = { shape: string; label: string; total: number; colors: ColorCount[]; unpainted: number };

export function ColorSummary({ panelColors, allPanelIds, onColorSelect }: ColorSummaryProps) {
  const shapeGroups = useMemo((): ShapeGroup[] => {
    const data = new Map<string, { colorCounts: Map<string, number>; total: number }>();

    for (const id of allPanelIds) {
      const shape = getPanelShape(id);
      if (!data.has(shape)) data.set(shape, { colorCounts: new Map(), total: 0 });
      const entry = data.get(shape)!;
      entry.total++;
      const color = panelColors[id];
      if (color) entry.colorCounts.set(color, (entry.colorCounts.get(color) ?? 0) + 1);
    }

    return Array.from(data.entries())
      .map(([shape, { colorCounts, total }]) => {
        const colors = Array.from(colorCounts.entries())
          .sort((a, b) => b[1] - a[1])
          .map(([color, count]) => ({ color, count }));
        const painted = colors.reduce((s, c) => s + c.count, 0);
        return { shape, label: SHAPE_LABELS[shape] ?? shape, total, colors, unpainted: total - painted };
      })
      .sort((a, b) => b.total - a.total);
  }, [panelColors, allPanelIds]);

  if (allPanelIds.length === 0) return null;

  return (
    <div style={styles.root}>
      {shapeGroups.map((group) => (
        <div key={group.shape} style={styles.card}>
          <div style={styles.cardHeader}>
            <span style={styles.shapeLabel}>{group.label}</span>
            <span style={styles.total}>{group.total} panels</span>
          </div>
          <div style={styles.colorList}>
            {group.colors.map(({ color, count }) => (
              <button
                key={color}
                style={styles.colorRow}
                onClick={() => onColorSelect(color)}
                title={`Select ${color}`}
              >
                <span style={{ ...styles.swatch, background: color }} />
                <span style={styles.hex}>{color}</span>
                <span style={styles.count}>{count}</span>
              </button>
            ))}
            {group.unpainted > 0 && (
              <div style={styles.unpaintedRow}>
                <span style={styles.swatchEmpty} />
                <span style={{ ...styles.hex, color: "var(--muted)" }}>default</span>
                <span style={styles.count}>{group.unpainted}</span>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

const styles = {
  root: {
    display: "flex",
    flexDirection: "column",
    gap: "8px",
  },
  card: {
    background: "#10131a",
    border: "1px solid var(--card-btn)",
    borderRadius: "8px",
    overflow: "hidden",
  },
  cardHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "7px 10px",
    borderBottom: "1px solid var(--card-btn)",
  },
  shapeLabel: {
    fontSize: "13px",
    fontWeight: 600,
    color: "var(--text)",
  },
  total: {
    fontSize: "11px",
    color: "var(--muted)",
  },
  colorList: {
    display: "flex",
    flexDirection: "column",
    gap: "1px",
    padding: "4px",
  },
  colorRow: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    padding: "4px 6px",
    background: "transparent",
    border: "none",
    borderRadius: "4px",
    cursor: "pointer",
    width: "100%",
    textAlign: "left",
  },
  unpaintedRow: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    padding: "4px 6px",
    opacity: 0.45,
  },
  swatch: {
    flexShrink: 0,
    width: "12px",
    height: "12px",
    borderRadius: "2px",
    border: "1px solid rgba(255,255,255,0.15)",
  },
  swatchEmpty: {
    flexShrink: 0,
    width: "12px",
    height: "12px",
    borderRadius: "2px",
    border: "1px dashed rgba(255,255,255,0.3)",
  },
  hex: {
    flex: 1,
    fontSize: "12px",
    color: "var(--text)",
    fontFamily: "monospace",
    letterSpacing: "0.03em",
  },
  count: {
    flexShrink: 0,
    fontSize: "12px",
    color: "var(--muted)",
    fontVariantNumeric: "tabular-nums",
  },
} satisfies Record<string, React.CSSProperties>;
