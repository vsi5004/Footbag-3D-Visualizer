import { memo, Suspense, useState, useEffect, useCallback } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import { FootbagModel } from "./FootbagModel.jsx";
import type { PanelColors } from "../../types.js";

interface FootbagCanvasProps {
  modelPath: string;
  panelColors: PanelColors;
  selectedPanelId: string | null;
  bgColor: string;
  textureEnabled: boolean;
  onPanelSelect: (panelId: string) => void;
  onPanelsDiscovered: (panels: string[]) => void;
  onDeselect: () => void;
}

// Module-level constants so R3F never sees a new object reference on re-render
const CAMERA_CONFIG = { position: [0, 0, 6] as [number, number, number], fov: 45 };
const GL_CONFIG = { antialias: true };

function Lights() {
  return (
    <>
      <ambientLight intensity={0.6} />
      <directionalLight position={[5, 8, 5]} intensity={1.2} />
      <directionalLight position={[-4, -2, -4]} intensity={0.3} color="#a0b0ff" />
    </>
  );
}

export const FootbagCanvas = memo(function FootbagCanvas({
  modelPath,
  panelColors,
  selectedPanelId,
  bgColor,
  textureEnabled,
  onPanelSelect,
  onPanelsDiscovered,
  onDeselect,
}: FootbagCanvasProps) {
  const [isLoading, setIsLoading] = useState(true);

  // Reset loading state whenever the model path changes
  useEffect(() => {
    setIsLoading(true);
  }, [modelPath]);

  const handlePanelsDiscovered = useCallback(
    (panels: string[]) => {
      setIsLoading(false);
      onPanelsDiscovered(panels);
    },
    [onPanelsDiscovered]
  );

  return (
    <div style={styles.wrapper}>
      {isLoading && (
        <div style={styles.loadingOverlay}>
          <svg style={styles.spinner} viewBox="0 0 40 40" fill="none">
            <circle cx="20" cy="20" r="16" stroke="#2a2f43" strokeWidth="4" />
            <circle cx="20" cy="20" r="16" stroke="#4ea1ff" strokeWidth="4"
              strokeDasharray="60 40" strokeLinecap="round" />
          </svg>
        </div>
      )}
      <Canvas
        camera={CAMERA_CONFIG}
        style={{ ...styles.canvas, background: bgColor }}
        gl={GL_CONFIG}
        onPointerMissed={onDeselect}
      >
        <Lights />
        <Suspense fallback={null}>
          <FootbagModel
            modelPath={modelPath}
            panelColors={panelColors}
            selectedPanelId={selectedPanelId}
            textureEnabled={textureEnabled}
            onPanelSelect={onPanelSelect}
            onPanelsDiscovered={handlePanelsDiscovered}
          />
        </Suspense>
        <OrbitControls enablePan={false} minDistance={3} maxDistance={12} />
      </Canvas>
    </div>
  );
});

const styles = {
  wrapper: {
    position: "relative",
    width: "100%",
    height: "100%",
  },
  canvas: {
    width: "100%",
    height: "100%",
  },
  loadingOverlay: {
    position: "absolute",
    inset: 0,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    zIndex: 1,
    pointerEvents: "none",
  },
  spinner: {
    width: "40px",
    height: "40px",
    animation: "spin 0.9s linear infinite",
  },
} satisfies Record<string, React.CSSProperties>;
