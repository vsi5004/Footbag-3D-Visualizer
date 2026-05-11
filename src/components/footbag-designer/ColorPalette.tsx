import type { PaletteEntry } from "../../types.js";

interface ColorPaletteProps {
  palette: PaletteEntry[];
  selectedColor: string;
  onColorSelect: (color: string) => void;
}

export function ColorPalette({ palette, selectedColor, onColorSelect }: ColorPaletteProps) {
  return (
    <div style={styles.root}>
      <div style={styles.grid}>
        {palette.map(({ id, label, color }) => {
          const isSelected = color === selectedColor;
          return (
            <button
              key={id}
              title={label}
              onClick={() => onColorSelect(color)}
              style={{
                ...styles.swatch,
                background: color,
                boxShadow: isSelected
                  ? "0 0 0 2px #0e0f12, 0 0 0 4px var(--accent)"
                  : "none",
              }}
              aria-label={label}
              aria-pressed={isSelected}
            />
          );
        })}
      </div>

      <div style={styles.pickerRow}>
        <label style={styles.pickerLabel} htmlFor="custom-color">
          Custom
        </label>
        <input
          id="custom-color"
          type="color"
          value={selectedColor}
          onChange={(e) => onColorSelect(e.target.value)}
          style={styles.picker}
          aria-label="Custom color picker"
        />
        <span style={styles.hex}>{selectedColor}</span>
      </div>
    </div>
  );
}

const styles = {
  root: {
    display: "flex",
    flexDirection: "column",
    gap: "12px",
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(6, 1fr)",
    gap: "5px",
  },
  swatch: {
    width: "100%",
    aspectRatio: "1",
    border: "1px solid var(--hover)",
    borderRadius: "5px",
    cursor: "pointer",
    padding: 0,
    transition: "box-shadow 0.15s",
  },
  pickerRow: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
  },
  pickerLabel: {
    fontSize: "13px",
    color: "var(--muted)",
    whiteSpace: "nowrap",
  },
  picker: {
    width: "32px",
    height: "28px",
    border: "1px solid var(--hover)",
    borderRadius: "5px",
    cursor: "pointer",
    padding: "2px",
    background: "var(--card-btn)",
  },
  hex: {
    fontSize: "12px",
    color: "var(--text)",
    fontFamily: "monospace",
  },
} satisfies Record<string, React.CSSProperties>;
