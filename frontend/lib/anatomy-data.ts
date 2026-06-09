/**
 * Anatomical structures metadata for 3D viewer labels and colors.
 * Mirrors backend anatomy_service.py structure IDs.
 *
 * Coordinate system (eye auto-centered to origin, diameter ≈ 2.2 units):
 *   +z  → anterior (cornea faces viewer)
 *   -z  → posterior (optic disc, retina)
 *   +x  → nasal (optic disc side for right eye)
 *   -x  → temporal (macula side)
 */

export type StructureLayer = "eye" | "pathway";

export interface StructureMeta {
  id: string;
  label: string;
  color: string;
  emissive: string;
  description: string;
  position: [number, number, number];
  scale: [number, number, number];
  shape: "sphere" | "cylinder";
  layer: StructureLayer;
}

/**
 * Semantic color scheme — encodes anatomical role, not just identity.
 *
 *  red    (#ff6b6b) — origin / photoreception (retina)
 *  gold   (#f0c040) — conduction (optic nerve)
 *  orange (#ff9f43) — decussation (chiasm)
 *  green  (#4ade80) — projection / tract (optic tract)
 *  blue   (#54a0ff) — relay (LGN)
 *  purple (#dda0dd) — radiation (optic radiations)
 *  cyan   (#74d7f7) — processing (visual cortex)
 */

export const STRUCTURES: StructureMeta[] = [
  // ── Eye layer — posterior structures ──────────────────────────────────────
  {
    id: "cornea",
    label: "Córnea",
    color: "#a8d8ea",
    emissive: "#2090c0",
    description: "Camada transparente anterior do olho",
    position: [0, 0, 1.05],
    scale: [0.42, 0.42, 0.42],
    shape: "sphere",
    layer: "eye",
  },
  {
    id: "retina",
    label: "Retina",
    color: "#ff6b6b",
    emissive: "#cc2200",
    description: "Tecido neural — extensão do SNC",
    position: [0, 0, 0],
    scale: [1.0, 1.0, 1.0],
    shape: "sphere",
    layer: "eye",
  },
  {
    // Temporal side, posterior pole
    id: "macula",
    label: "Mácula / Fóvea",
    color: "#f0a500",
    emissive: "#b07000",
    description: "Centro da visão de alta resolução",
    position: [-0.18, 0, -0.82],
    scale: [0.16, 0.16, 0.16],
    shape: "sphere",
    layer: "eye",
  },
  {
    // Nasal side, posterior pole — root of the visual pathway
    id: "disco_optico",
    label: "Disco Óptico",
    color: "#f7dc6f",
    emissive: "#b09820",
    description: "Saída do nervo óptico — ponto cego",
    position: [0.38, 0, -0.88],
    scale: [0.14, 0.14, 0.14],
    shape: "sphere",
    layer: "eye",
  },

  // ── Visual pathway — always visible ───────────────────────────────────────
  {
    id: "nervo_optico",
    label: "Nervo Óptico",
    color: "#f0c040",
    emissive: "#c08000",
    description: "II par craniano — fibras do SNC",
    position: [0.22, 0, -2.0],
    scale: [0.18, 0.18, 0.9],
    shape: "cylinder",
    layer: "pathway",
  },
  {
    id: "quiasma_optico",
    label: "Quiasma Óptico",
    color: "#ff9f43",
    emissive: "#cc5500",
    description: "Cruzamento das fibras nasais",
    position: [0, 0, -3.8],
    scale: [0.52, 0.22, 0.22],
    shape: "sphere",
    layer: "pathway",
  },
  {
    id: "trato_optico",
    label: "Trato Óptico",
    color: "#4ade80",
    emissive: "#20a040",
    description: "Via retroquiasmática",
    position: [0.55, 0.1, -4.5],
    scale: [0.12, 0.12, 0.65],
    shape: "cylinder",
    layer: "pathway",
  },
  {
    id: "corpo_geniculado_lateral",
    label: "Corpo Geniculado Lateral",
    color: "#54a0ff",
    emissive: "#1060cc",
    description: "Estação talâmica da via visual",
    position: [0.65, 0.15, -5.0],
    scale: [0.24, 0.24, 0.24],
    shape: "sphere",
    layer: "pathway",
  },
  {
    id: "radiacoes_opticas",
    label: "Radiações Ópticas",
    color: "#dda0dd",
    emissive: "#9040a0",
    description: "CGL → Córtex visual V1",
    position: [0.4, 0.2, -5.8],
    scale: [0.1, 0.1, 0.75],
    shape: "cylinder",
    layer: "pathway",
  },
  {
    id: "cortex_visual",
    label: "Córtex Visual (V1)",
    color: "#74d7f7",
    emissive: "#1090c0",
    description: "Lobo occipital — processamento visual primário",
    position: [0, 0.3, -6.6],
    scale: [0.58, 0.35, 0.3],
    shape: "sphere",
    layer: "pathway",
  },
];

export const STRUCTURE_MAP = new Map(STRUCTURES.map((s) => [s.id, s]));
