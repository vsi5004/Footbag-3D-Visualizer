import { MODEL_ORDER } from "../../data/modelRegistry.js";
import type { ModelConfig, ModelType } from "../../types.js";

interface ModelSelectorProps {
  models: Record<ModelType, ModelConfig>;
  currentType: ModelType;
  onSelect: (type: ModelType) => void;
}

export function ModelSelector({ models, currentType, onSelect }: ModelSelectorProps) {
  return (
    <div style={styles.strip}>
      {MODEL_ORDER.map((id, i) => {
        const model = models[id];
        const isActive = id === currentType;
        const isFirst = i === 0;
        const isLast = i === MODEL_ORDER.length - 1;
        return (
          <button
            key={id}
            onClick={() => onSelect(id)}
            disabled={!model.available}
            title={`${model.label} — ${model.description}`}
            style={{
              ...styles.segment,
              ...(isFirst ? styles.segmentFirst : {}),
              ...(isLast ? styles.segmentLast : {}),
              ...(isActive ? styles.segmentActive : {}),
              ...(!model.available ? styles.segmentDisabled : {}),
            }}
          >
            {id}
          </button>
        );
      })}
    </div>
  );
}

const styles = {
  strip: {
    display: "flex",
    width: "100%",
  },
  segment: {
    flex: 1,
    padding: "7px 0",
    background: "var(--card-btn)",
    borderTop: "1px solid var(--hover)",
    borderRight: "1px solid var(--hover)",
    borderBottom: "1px solid var(--hover)",
    borderLeft: "none",
    color: "var(--text)",
    fontSize: "13px",
    fontWeight: 500,
    cursor: "pointer",
    textAlign: "center",
    transition: "background-color 0.15s, color 0.15s",
  },
  segmentFirst: {
    borderLeft: "1px solid var(--hover)",
    borderRadius: "6px 0 0 6px",
  },
  segmentLast: {
    borderRadius: "0 6px 6px 0",
  },
  segmentActive: {
    background: "var(--accent)",
    borderTop: "1px solid var(--accent)",
    borderRight: "1px solid var(--accent)",
    borderBottom: "1px solid var(--accent)",
    color: "#001a33",
    fontWeight: 700,
    zIndex: 1,
  },
  segmentDisabled: {
    opacity: 0.3,
    cursor: "not-allowed",
  },
} satisfies Record<string, React.CSSProperties>;
