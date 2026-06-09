"use client";

/**
 * NeuroVision — 3D Eye Viewer
 *
 * Architecture:
 *   <EyeViewer3D>              — manages hoveredFiberRegion state + DOM tooltip
 *     <Canvas>
 *       <Scene>
 *         <EyeModel />           — GLTF, auto-centered
 *         <ExtraocularMuscles /> — 4 rectus muscles, merged geometry (1 draw call)
 *         <group "visual-pathway">
 *           <NerveFiberBundle /> — 10 interactive fiber strands (5 regions × 2)
 *           <VisualPathwayTube /> — chiasm → cortex
 *           <AnatomicalStructure /> × 10
 *         </group>
 *       </Scene>
 *     </Canvas>
 *     <FiberRegionTooltip />    — DOM overlay, appears on fiber hover
 *
 * LOD strategy:
 *   - Muscles merged into 1 draw call via mergeGeometries
 *   - Tube segments reduced ~40% (visual quality unchanged at education scale)
 *   - Structure spheres: 32→16 segments
 *   - Fiber hit zones: invisible thick tube wrapping each strand (easier to click)
 */

import { useRef, useState, useCallback, Suspense, useMemo } from "react";
import { Canvas, useFrame, ThreeEvent } from "@react-three/fiber";
import { OrbitControls, Text, useGLTF } from "@react-three/drei";
import * as THREE from "three";
import { mergeGeometries } from "three/examples/jsm/utils/BufferGeometryUtils.js";
import { STRUCTURES, STRUCTURE_MAP, StructureMeta } from "@/lib/anatomy-data";
import { FIBER_REGIONS, FIBER_REGION_MAP } from "@/lib/fiber-region-data";

// ── Constants ─────────────────────────────────────────────────────────────────

const DISC = STRUCTURE_MAP.get("disco_optico")!;
const DISC_POSITION = new THREE.Vector3(...DISC.position);

// ── GLTF Eye Model ────────────────────────────────────────────────────────────

function EyeModel() {
  const { scene } = useGLTF("/models/eye.glb");

  const { scale, offset } = useMemo(() => {
    const box = new THREE.Box3().setFromObject(scene);
    const size = new THREE.Vector3();
    box.getSize(size);
    const maxDim = Math.max(size.x, size.y, size.z);
    const s = maxDim > 0 ? 2.2 / maxDim : 1;
    const center = new THREE.Vector3();
    box.getCenter(center);

    scene.traverse((child) => {
      if (!(child as THREE.Mesh).isMesh) return;
      const mesh = child as THREE.Mesh;
      const mats = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
      mats.forEach((mat) => {
        const m = mat as THREE.MeshStandardMaterial;
        if (!m.color) return;
        const { r, g, b } = m.color;
        if (r > 0.45 && r > g * 1.5 && r > b * 1.5) {
          m.transparent = true;
          m.opacity = 0.08;
          m.needsUpdate = true;
        }
      });
    });

    return { scale: s, offset: center.multiplyScalar(-s) };
  }, [scene]);

  return (
    <group scale={[scale, scale, scale]} position={[offset.x, offset.y, offset.z]}>
      <primitive object={scene} />
    </group>
  );
}

function EyeFallback() {
  return (
    <group>
      <mesh>
        <sphereGeometry args={[1, 40, 40]} />
        <meshStandardMaterial color="#f0ebe3" roughness={0.45} />
      </mesh>
      <mesh position={[0, 0, 0.9]}>
        <circleGeometry args={[0.42, 48]} />
        <meshStandardMaterial color="#2d6ea8" roughness={0.3} />
      </mesh>
      <mesh position={[0, 0, 0.91]}>
        <circleGeometry args={[0.16, 32]} />
        <meshStandardMaterial color="#050505" />
      </mesh>
    </group>
  );
}

// ── Extraocular Muscles ───────────────────────────────────────────────────────
// 4 rectus muscles merged into 1 draw call via mergeGeometries.
// Segments reduced: tubularSegments 24→12, radialSegments 8→5.

const RECTUS_ANGLES = [
  Math.PI / 2,   // superior rectus
  -Math.PI / 2,  // inferior rectus
  0,             // medial rectus (nasal)
  Math.PI,       // lateral rectus (temporal)
];

function ExtraocularMuscles() {
  const geo = useMemo(() => {
    const geos = RECTUS_ANGLES.map((angle) => {
      const sx = Math.sin(angle);
      const sy = Math.cos(angle);
      const r = 1.06;
      const pts = [
        new THREE.Vector3(sx * 0.15, sy * 0.15, -1.55),
        new THREE.Vector3(sx * 0.55, sy * 0.55, -1.1),
        new THREE.Vector3(sx * 0.92, sy * 0.92, -0.35),
        new THREE.Vector3(sx * r,    sy * r,     0.35),
      ];
      return new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 12, 0.065, 5, false);
    });
    const merged = mergeGeometries(geos);
    geos.forEach((g) => g.dispose());
    return merged;
  }, []);

  return (
    <mesh geometry={geo}>
      <meshStandardMaterial
        color="#c0392b"
        emissive="#6a0a00"
        emissiveIntensity={0.15}
        transparent
        opacity={0.72}
        roughness={0.55}
      />
    </mesh>
  );
}

// ── Nerve Fiber Bundle ────────────────────────────────────────────────────────
// 5 regions × 2 strands = 10 fibers, each interactive.
// Each strand has an invisible wider hit zone for comfortable hover/click.

interface NerveFiberBundleProps {
  hoveredRegion: string | null;
  onRegionHover: (id: string | null) => void;
  onRegionClick?: (id: string) => void;
}

function NerveFiberBundle({ hoveredRegion, onRegionHover, onRegionClick }: NerveFiberBundleProps) {
  const fibers = useMemo(() => {
    const [dx, dy, dz] = DISC_POSITION.toArray();
    const spread = 0.028;

    return FIBER_REGIONS.flatMap((region) =>
      region.angles.map((angle) => {
        const ox = Math.cos(angle) * spread;
        const oy = Math.sin(angle) * spread;
        const pts = [
          new THREE.Vector3(dx + ox,             dy + oy,      dz),
          new THREE.Vector3(dx * 0.85 + ox,      oy * 0.6,     dz - 0.55),
          new THREE.Vector3(dx * 0.5 + ox * 0.4, 0,            -2.0),
          new THREE.Vector3(dx * 0.1,             0,            -3.2),
          new THREE.Vector3(0,                    0,            -3.8),
        ];
        const curve = new THREE.CatmullRomCurve3(pts);
        return {
          visGeo: new THREE.TubeGeometry(curve, 24, 0.007, 4, false),
          hitGeo: new THREE.TubeGeometry(curve, 12, 0.038, 4, false),
          regionId: region.id,
          regionColor: region.color,
        };
      })
    );
  }, []);

  return (
    <>
      {fibers.map(({ visGeo, hitGeo, regionId, regionColor }, i) => {
        const isActive  = hoveredRegion === regionId;
        const isDimmed  = hoveredRegion !== null && !isActive;
        return (
          <group key={i}>
            {/* Invisible wide hit zone */}
            <mesh
              geometry={hitGeo}
              onClick={(e: ThreeEvent<MouseEvent>) => {
                e.stopPropagation();
                onRegionClick?.(regionId);
              }}
              onPointerOver={(e: ThreeEvent<PointerEvent>) => {
                e.stopPropagation();
                onRegionHover(regionId);
                document.body.style.cursor = "pointer";
              }}
              onPointerOut={() => {
                onRegionHover(null);
                document.body.style.cursor = "default";
              }}
            >
              <meshBasicMaterial transparent opacity={0} depthWrite={false} />
            </mesh>
            {/* Visible strand */}
            <mesh geometry={visGeo}>
              <meshStandardMaterial
                color={isActive ? regionColor : isDimmed ? "#6b5e30" : "#f5e6a3"}
                emissive={isActive ? regionColor : isDimmed ? "#2a2000" : "#b09030"}
                emissiveIntensity={isActive ? 0.7 : isDimmed ? 0.05 : 0.2}
                transparent
                opacity={isActive ? 1.0 : isDimmed ? 0.28 : 0.7}
                roughness={0.3}
              />
            </mesh>
          </group>
        );
      })}
    </>
  );
}

// ── Visual Pathway Tube ───────────────────────────────────────────────────────
// Chiasm → cortex only. Segments reduced: 50→32 tubular, 10→8 radial.

function VisualPathwayTube() {
  const meshRef = useRef<THREE.Mesh>(null);

  const geo = useMemo(() => {
    const pts = [
      new THREE.Vector3(0,    0,    -3.8),
      new THREE.Vector3(0.55, 0.1,  -4.5),
      new THREE.Vector3(0.65, 0.15, -5.0),
      new THREE.Vector3(0.4,  0.2,  -5.8),
      new THREE.Vector3(0,    0.3,  -6.6),
    ];
    return new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 32, 0.032, 8, false);
  }, []);

  useFrame(() => {
    if (meshRef.current) {
      const mat = meshRef.current.material as THREE.MeshStandardMaterial;
      mat.emissiveIntensity = 0.2 + Math.sin(Date.now() * 0.0018) * 0.08;
    }
  });

  return (
    <mesh ref={meshRef} geometry={geo}>
      <meshStandardMaterial
        color="#8ecae6"
        emissive="#1a5f80"
        emissiveIntensity={0.25}
        transparent
        opacity={0.38}
      />
    </mesh>
  );
}

// ── Anatomy Structure Overlay ─────────────────────────────────────────────────
// Sphere segments reduced 32→16 (75% vertex reduction, imperceptible at this size).

interface StructureProps {
  meta: StructureMeta;
  isSelected: boolean;
  isHovered: boolean;
  onClick: (id: string) => void;
  onHover: (id: string | null) => void;
}

function AnatomicalStructure({ meta, isSelected, isHovered, onClick, onHover }: StructureProps) {
  const meshRef = useRef<THREE.Mesh>(null);
  const active = isSelected || isHovered;
  const isEye = meta.layer === "eye";
  const isCylinder = meta.shape === "cylinder";

  useFrame((_, delta) => {
    if (meshRef.current && isSelected) meshRef.current.rotation.y += delta * 0.6;
  });

  const opacity  = isEye
    ? (isSelected ? 0.38 : isHovered ? 0.22 : 0.0)
    : (isSelected ? 0.92 : isHovered ? 0.85 : 0.72);
  const emissive = isEye
    ? (isSelected ? 0.8 : isHovered ? 0.5 : 0.0)
    : (isSelected ? 0.75 : isHovered ? 0.45 : 0.18);

  const meshScale = isCylinder
    ? new THREE.Vector3(meta.scale[0], meta.scale[2] * 3, meta.scale[0])
    : new THREE.Vector3(...meta.scale);

  const meshRot: [number, number, number] = isCylinder ? [Math.PI / 2, 0, 0] : [0, 0, 0];

  return (
    <group position={new THREE.Vector3(...meta.position)}>
      {isEye && !active && (
        <mesh
          onClick={(e: ThreeEvent<MouseEvent>) => { e.stopPropagation(); onClick(meta.id); }}
          onPointerOver={(e: ThreeEvent<PointerEvent>) => { e.stopPropagation(); onHover(meta.id); document.body.style.cursor = "pointer"; }}
          onPointerOut={() => { onHover(null); document.body.style.cursor = "default"; }}
        >
          <sphereGeometry args={[meta.scale[0] * 1.2, 10, 10]} />
          <meshBasicMaterial transparent opacity={0} depthWrite={false} />
        </mesh>
      )}

      <mesh
        ref={meshRef}
        scale={meshScale}
        rotation={meshRot}
        visible={!isEye || active}
        onClick={(e: ThreeEvent<MouseEvent>) => { e.stopPropagation(); onClick(meta.id); }}
        onPointerOver={(e: ThreeEvent<PointerEvent>) => { e.stopPropagation(); onHover(meta.id); document.body.style.cursor = "pointer"; }}
        onPointerOut={() => { onHover(null); document.body.style.cursor = "default"; }}
      >
        {isCylinder
          ? <cylinderGeometry args={[1, 1, 1, 12]} />
          : <sphereGeometry args={[1, 16, 16]} />}
        <meshStandardMaterial
          color={meta.color}
          emissive={meta.emissive}
          emissiveIntensity={emissive}
          transparent
          opacity={opacity}
          roughness={0.2}
          metalness={0.05}
          depthWrite={!isEye}
        />
      </mesh>

      {active && (
        <Text
          position={[0, (meta.scale[1] || meta.scale[0]) + 0.35, 0]}
          fontSize={0.18}
          color={meta.color}
          anchorX="center"
          anchorY="bottom"
          renderOrder={3}
          outlineWidth={0.012}
          outlineColor="#050d1a"
        >
          {meta.label}
        </Text>
      )}

      {isSelected && (
        <mesh
          scale={isCylinder
            ? new THREE.Vector3(meta.scale[0] * 1.7, meta.scale[2] * 3.6, meta.scale[0] * 1.7)
            : new THREE.Vector3(meta.scale[0] * 1.55, meta.scale[1] * 1.55, meta.scale[2] * 1.55)}
          rotation={meshRot}
        >
          {isCylinder
            ? <cylinderGeometry args={[1, 1, 1, 12]} />
            : <sphereGeometry args={[1, 12, 12]} />}
          <meshStandardMaterial
            color={meta.color}
            emissive={meta.emissive}
            emissiveIntensity={0.5}
            transparent
            opacity={isEye ? 0.18 : 0.09}
            wireframe
          />
        </mesh>
      )}
    </group>
  );
}

// ── Fiber Region Tooltip ──────────────────────────────────────────────────────
// DOM overlay rendered outside Canvas — shows mini VF diagram on fiber hover.

function FiberRegionTooltip({ regionId }: { regionId: string }) {
  const region = FIBER_REGION_MAP.get(regionId);
  if (!region) return null;
  const clipId = `tip-clip-${regionId}`;

  return (
    <div
      style={{
        background: "rgba(5,13,26,0.93)",
        border: `1px solid ${region.color}50`,
        borderRadius: "12px",
        padding: "10px 12px",
        minWidth: "180px",
        boxShadow: `0 4px 20px rgba(0,0,0,0.5), 0 0 0 1px ${region.color}18`,
      }}
    >
      <p style={{ color: region.color, fontSize: "11px", fontWeight: 700, marginBottom: 2 }}>
        {region.label}
      </p>
      <p style={{ color: "rgba(255,255,255,0.4)", fontSize: "9px", marginBottom: 8 }}>
        {region.retinalQuadrant}
      </p>

      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        {/* Mini OD visual field patch */}
        <svg width={52} height={52} viewBox="0 0 90 90" style={{ flexShrink: 0 }}>
          <defs><clipPath id={clipId}><circle cx="45" cy="45" r="42" /></clipPath></defs>
          <circle cx="45" cy="45" r="42" fill="rgba(4,11,22,0.95)" stroke={`${region.color}45`} strokeWidth="1.5" />
          <line x1="45" y1="4" x2="45" y2="86" stroke="rgba(255,255,255,0.1)" strokeWidth="0.7" />
          <line x1="4" y1="45" x2="86" y2="45" stroke="rgba(255,255,255,0.1)" strokeWidth="0.7" />
          <circle cx="45" cy="45" r="14" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="0.5" />
          {region.od.map((s, i) => {
            const common = { fill: region.color, opacity: 0.78 as number, clipPath: `url(#${clipId})` };
            if (s.type === "path" && s.d) return <path key={i} d={s.d} {...common} />;
            if (s.type === "circle") return <circle key={i} cx={s.cx} cy={s.cy} r={s.r} {...common} />;
            return null;
          })}
          <circle cx="45" cy="45" r="2.2" fill="rgba(255,255,255,0.55)" />
        </svg>

        <div>
          <p style={{ color: "rgba(255,255,255,0.55)", fontSize: "9px" }}>Campo OD</p>
          {region.crossesAtChiasm && (
            <p style={{ color: "#ff9f43", fontSize: "9px", marginTop: 3, display: "flex", alignItems: "center", gap: 3 }}>
              ↕ Cruza no quiasma
            </p>
          )}
          <p style={{ color: "rgba(255,255,255,0.28)", fontSize: "9px", marginTop: 5 }}>
            clique para detalhes
          </p>
        </div>
      </div>
    </div>
  );
}

// ── Scene ─────────────────────────────────────────────────────────────────────

interface SceneProps {
  selectedId: string | null;
  onSelect: (id: string | null) => void;
  onFiberRegionHover: (id: string | null) => void;
  onFiberRegionClick?: (id: string) => void;
}

function Scene({ selectedId, onSelect, onFiberRegionHover, onFiberRegionClick }: SceneProps) {
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const [hoveredFiber, setHoveredFiber] = useState<string | null>(null);

  const handleClick    = useCallback((id: string) => onSelect(id === selectedId ? null : id), [selectedId, onSelect]);
  const handleFiberHover = useCallback((id: string | null) => {
    setHoveredFiber(id);
    onFiberRegionHover(id);
  }, [onFiberRegionHover]);

  const eyeStructures     = STRUCTURES.filter((s) => s.layer === "eye");
  const pathwayStructures = STRUCTURES.filter((s) => s.layer === "pathway");

  return (
    <>
      <ambientLight intensity={0.5} />
      <pointLight position={[5,   4,  6]}  intensity={1.8} color="#ffffff" />
      <pointLight position={[-4, -2,  4]}  intensity={0.7} color="#b0e0ff" />
      <pointLight position={[0,   3, -5]}  intensity={0.5} color="#ffe066" />
      <pointLight position={[2,  -3,  1]}  intensity={0.4} color="#ffbbbb" />

      <Suspense fallback={<EyeFallback />}>
        <EyeModel />
      </Suspense>

      <ExtraocularMuscles />

      {eyeStructures.map((meta) => (
        <AnatomicalStructure
          key={meta.id}
          meta={meta}
          isSelected={selectedId === meta.id}
          isHovered={hoveredId === meta.id}
          onClick={handleClick}
          onHover={setHoveredId}
        />
      ))}

      <group name="visual-pathway">
        <NerveFiberBundle
          hoveredRegion={hoveredFiber}
          onRegionHover={handleFiberHover}
          onRegionClick={onFiberRegionClick}
        />
        <VisualPathwayTube />

        {pathwayStructures.map((meta) => (
          <AnatomicalStructure
            key={meta.id}
            meta={meta}
            isSelected={selectedId === meta.id}
            isHovered={hoveredId === meta.id}
            onClick={handleClick}
            onHover={setHoveredId}
          />
        ))}
      </group>

      <OrbitControls
        enablePan={false}
        minDistance={3}
        maxDistance={18}
        autoRotate={!selectedId}
        autoRotateSpeed={0.45}
        target={[0, 0, -2.5]}
      />
    </>
  );
}

// ── Export ────────────────────────────────────────────────────────────────────

interface EyeViewer3DProps {
  selectedStructure: string | null;
  onStructureSelect: (id: string | null) => void;
  onFiberRegionClick?: (id: string) => void;
}

export default function EyeViewer3D({ selectedStructure, onStructureSelect, onFiberRegionClick }: EyeViewer3DProps) {
  const [hoveredFiberRegion, setHoveredFiberRegion] = useState<string | null>(null);

  return (
    <div className="w-full h-full relative">
      <div className="absolute top-4 left-1/2 -translate-x-1/2 z-10 pointer-events-none">
        <p className="text-xs text-center" style={{ color: "var(--text-muted)" }}>
          Clique em uma estrutura para explorar · Passe o cursor nas fibras para mapear o campo visual
        </p>
      </div>

      <Canvas
        camera={{ position: [-1.5, 0.8, 5.5], fov: 52 }}
        gl={{ antialias: true, alpha: true }}
        style={{ background: "transparent" }}
        onPointerMissed={() => onStructureSelect(null)}
      >
        <Scene
          selectedId={selectedStructure}
          onSelect={onStructureSelect}
          onFiberRegionHover={setHoveredFiberRegion}
          onFiberRegionClick={onFiberRegionClick}
        />
      </Canvas>

      {/* Fiber region tooltip — DOM overlay, appears on hover */}
      {hoveredFiberRegion && (
        <div className="absolute bottom-12 left-4 z-20 pointer-events-none animate-fade-in-up">
          <FiberRegionTooltip regionId={hoveredFiberRegion} />
        </div>
      )}

      <div className="absolute bottom-4 left-4 z-10">
        <p className="text-xs" style={{ color: "var(--text-muted)" }}>
          {STRUCTURES.length} estruturas · {FIBER_REGIONS.length} regiões de fibra
        </p>
      </div>
    </div>
  );
}

useGLTF.preload("/models/eye.glb");
