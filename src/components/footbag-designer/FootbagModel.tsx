import { useEffect, useMemo, useCallback, useRef, useState } from "react";
import { useGLTF } from "@react-three/drei";
import * as THREE from "three";
import type { ThreeEvent } from "@react-three/fiber";
import type { PanelColors } from "../../types.js";

interface FootbagModelProps {
  modelPath: string;
  panelColors: PanelColors;
  selectedPanelId: string | null;
  textureEnabled: boolean;
  onPanelSelect: (panelId: string) => void;
  onPanelsDiscovered: (panels: string[]) => void;
}

const EDGE_THRESHOLD_ANGLE = 30;
const TEXTURE_REPEAT = 0.2;

const base = import.meta.env.BASE_URL;
const NORMAL_MAP_URL = `${base}textures/suede_normal.png`;
const ROUGHNESS_MAP_URL = `${base}textures/suede_roughness.png`;

function isPanelMesh(obj: THREE.Object3D): obj is THREE.Mesh {
  return obj instanceof THREE.Mesh && obj.name.startsWith("panel_");
}

function generatePanelUVs(geometry: THREE.BufferGeometry, meshName: string): void {
  const pos = geometry.attributes.position;
  if (!pos) return;

  const center = new THREE.Vector3();
  const vertex = new THREE.Vector3();
  for (let i = 0; i < pos.count; i++) {
    vertex.fromBufferAttribute(pos, i);
    center.add(vertex);
  }
  center.divideScalar(pos.count).normalize();

  const helper = Math.abs(center.dot(new THREE.Vector3(0, 0, 1))) < 0.9
    ? new THREE.Vector3(0, 0, 1)
    : new THREE.Vector3(1, 0, 0);
  const baseTanU = new THREE.Vector3().crossVectors(center, helper).normalize();
  const baseTanV = new THREE.Vector3().crossVectors(center, baseTanU).normalize();

  // Rotate the UV frame by a deterministic per-panel angle so each panel's
  // grain direction differs, breaking up the aligned-stripe artifact.
  const hash = meshName.split("").reduce((acc, c) => acc + c.charCodeAt(0), 0);
  const angle = (hash % 360) * (Math.PI / 180);
  const cos = Math.cos(angle);
  const sin = Math.sin(angle);
  const tanU = new THREE.Vector3().addScaledVector(baseTanU, cos).addScaledVector(baseTanV, sin);
  const tanV = new THREE.Vector3().addScaledVector(baseTanU, -sin).addScaledVector(baseTanV, cos);

  const uvs = new Float32Array(pos.count * 2);
  for (let i = 0; i < pos.count; i++) {
    vertex.fromBufferAttribute(pos, i);
    uvs[i * 2]     = vertex.dot(tanU);
    uvs[i * 2 + 1] = vertex.dot(tanV);
  }
  geometry.setAttribute("uv", new THREE.BufferAttribute(uvs, 2));
}

export function FootbagModel({
  modelPath,
  panelColors,
  selectedPanelId,
  textureEnabled,
  onPanelSelect,
  onPanelsDiscovered,
}: FootbagModelProps) {
  const { scene } = useGLTF(modelPath);
  const [normalMap, setNormalMap] = useState<THREE.Texture | null>(null);
  const [roughnessMap, setRoughnessMap] = useState<THREE.Texture | null>(null);

  // Load textures manually so a missing file never crashes the model
  useEffect(() => {
    const loader = new THREE.TextureLoader();
    const configure = (tex: THREE.Texture) => {
      tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
      tex.repeat.set(TEXTURE_REPEAT, TEXTURE_REPEAT);
      tex.needsUpdate = true;
    };
    loader.load(NORMAL_MAP_URL, (tex) => {
      tex.colorSpace = THREE.NoColorSpace;
      configure(tex);
      setNormalMap(tex);
    }, undefined, () => console.warn("Suede normal map failed to load"));
    loader.load(ROUGHNESS_MAP_URL, (tex) => {
      configure(tex);
      setRoughnessMap(tex);
    }, undefined, () => console.warn("Suede roughness map failed to load"));
  }, []);

  const { clonedScene, panelMeshes, edgeMat } = useMemo(() => {
    const cloned = scene.clone(true);
    const meshes = new Map<string, THREE.Mesh>();
    const lineMat = new THREE.LineBasicMaterial({ color: "#ffffff" });

    cloned.traverse((obj) => {
      if (!isPanelMesh(obj)) return;

      generatePanelUVs(obj.geometry, obj.name);

      const mat = (obj.material as THREE.MeshStandardMaterial).clone();
      obj.userData.originalColor = mat.color.clone();
      mat.metalness = 0.0;
      // Push panel surfaces back slightly so edge lines render in front without z-fighting
      mat.polygonOffset = true;
      mat.polygonOffsetFactor = 1;
      mat.polygonOffsetUnits = 1;
      obj.material = mat;

      const edgeLines = new THREE.LineSegments(
        new THREE.EdgesGeometry(obj.geometry, EDGE_THRESHOLD_ANGLE),
        lineMat
      );
      edgeLines.visible = false;
      // Exclude from raycasting — purely visual
      edgeLines.raycast = () => {};
      obj.add(edgeLines);
      obj.userData.edgeLines = edgeLines;

      meshes.set(obj.name, obj);
    });

    return { clonedScene: cloned, panelMeshes: meshes, edgeMat: lineMat };
  }, [scene]);

  // Apply or remove suede texture maps reactively — no scene rebuild needed
  useEffect(() => {
    panelMeshes.forEach((mesh) => {
      const mat = mesh.material as THREE.MeshStandardMaterial;
      if (textureEnabled) {
        mat.normalMap = normalMap;
        mat.normalScale = new THREE.Vector2(3.0, 3.0);
        mat.roughnessMap = roughnessMap;
        mat.roughness = 1.0;
      } else {
        mat.normalMap = null;
        mat.roughnessMap = null;
        mat.roughness = 0.85;
      }
      mat.needsUpdate = true;
    });
  }, [panelMeshes, textureEnabled, normalMap, roughnessMap]);

  useEffect(() => {
    onPanelsDiscovered(Array.from(panelMeshes.keys()));
  }, [panelMeshes, onPanelsDiscovered]);

  // Dispose cloned materials and edge geometries — textures are cached/shared, not owned here
  useEffect(() => {
    return () => {
      panelMeshes.forEach((mesh) => {
        (mesh.material as THREE.MeshStandardMaterial).dispose();
        (mesh.userData.edgeLines as THREE.LineSegments).geometry.dispose();
      });
      edgeMat.dispose();
    };
  }, [panelMeshes, edgeMat]);

  useEffect(() => {
    panelMeshes.forEach((mesh, panelId) => {
      const mat = mesh.material as THREE.MeshStandardMaterial;
      const originalColor = mesh.userData.originalColor as THREE.Color;
      const userColor = panelColors[panelId];
      if (userColor) {
        mat.color.set(userColor);
      } else {
        mat.color.copy(originalColor);
      }

      const edgeLines = mesh.userData.edgeLines as THREE.LineSegments;
      edgeLines.visible = panelId === selectedPanelId;
    });
  }, [panelMeshes, panelColors, selectedPanelId]);

  const pointerDownPos = useRef<{ x: number; y: number } | null>(null);

  const handlePointerDown = useCallback((e: ThreeEvent<PointerEvent>) => {
    pointerDownPos.current = { x: e.clientX, y: e.clientY };
  }, []);

  const handleClick = useCallback(
    (e: ThreeEvent<MouseEvent>) => {
      e.stopPropagation();
      const down = pointerDownPos.current;
      if (down) {
        const dx = e.clientX - down.x;
        const dy = e.clientY - down.y;
        if (dx * dx + dy * dy > 25) return;
      }
      if (isPanelMesh(e.object)) {
        onPanelSelect(e.object.name);
      }
    },
    [onPanelSelect]
  );

  const handlePointerOver = useCallback((e: ThreeEvent<PointerEvent>) => {
    if (isPanelMesh(e.object)) {
      document.body.style.cursor = "pointer";
    }
  }, []);

  const handlePointerOut = useCallback(() => {
    document.body.style.cursor = "auto";
  }, []);

  return (
    <primitive
      object={clonedScene}
      onPointerDown={handlePointerDown}
      onClick={handleClick}
      onPointerOver={handlePointerOver}
      onPointerOut={handlePointerOut}
    />
  );
}
