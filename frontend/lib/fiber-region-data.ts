/**
 * NeuroVision — Fiber Region Data
 *
 * Maps retinal quadrant → optic nerve fiber region → visual field patch.
 *
 * Each region contains 2 fiber strands defined by angles at the optic disc face.
 * Coordinate system (right eye, +x nasal, +y superior, disc at +x pole):
 *   angle = 0°   (+x, 0)  — nasal meridian
 *   angle = 90°  (0, +y)  — superior meridian
 *   angle = 180° (−x, 0)  — temporal (macular) direction
 *   angle = 270° (0, −y)  — inferior meridian
 *
 * Retinotopic rule (image inverted by lens):
 *   Superior retina → inferior visual field
 *   Nasal retina    → temporal visual field  (nasal fibers CROSS at chiasm)
 *   Temporal retina → nasal visual field    (temporal fibers STAY ipsilateral)
 *
 * Visual field SVG convention (same as visual-field-data.ts):
 *   viewBox "0 0 90 90", center cx=45 cy=45 r=42
 *   OD diagram: LEFT = nasal visual field, RIGHT = temporal visual field
 *   Defects shown for a RIGHT optic nerve lesion (pre-chiasmatic → OD only).
 */

import type { VFShape } from "./visual-field-data";

// ── SVG path primitives ───────────────────────────────────────────────────────
// Identical coordinate system to visual-field-data.ts P constant.

const P = {
  topLeft:     "M 45,3  A 42,42 0 0,0 3,45  L 45,45 Z",
  topRight:    "M 45,3  A 42,42 0 0,1 87,45 L 45,45 Z",
  bottomLeft:  "M 3,45  A 42,42 0 0,0 45,87 L 45,45 Z",
  bottomRight: "M 87,45 A 42,42 0 0,0 45,87 L 45,45 Z",
} as const;

const DEG = Math.PI / 180;

// ── Types ─────────────────────────────────────────────────────────────────────

export interface FiberRegionData {
  id: string;
  label: string;
  /** Human-readable origin in the retina */
  retinalQuadrant: string;
  /** Educational description of the defect produced by a lesion in this region */
  description: string;
  /** Semantic color matching anatomy-data.ts scheme */
  color: string;
  /** Nasal fibers cross at the optic chiasm → contralateral optic tract */
  crossesAtChiasm: boolean;
  /**
   * Two angles (radians) for the 2 fiber strands of this region.
   * Computed as angular position at the optic disc face — see header notes.
   */
  angles: [number, number];
  /** Visual field patch for OD (right optic nerve, pre-chiasmatic) */
  od: VFShape[];
  /** Left eye — empty for pre-chiasmatic lesions */
  oe: VFShape[];
}

// ── Data ─────────────────────────────────────────────────────────────────────

export const FIBER_REGIONS: FiberRegionData[] = [
  // ── Superior nasal ───────────────────────────────────────────────────────
  // Nasal retina → temporal VF; superior retina → inferior VF
  // → inferior temporal of OD diagram = bottomRight
  // Nasal → crosses at chiasm
  {
    id: "sup_nasal",
    label: "Fibras Sup. Nasais",
    retinalQuadrant: "Quadrante retinal superior nasal",
    description:
      "Fibras da retina superior nasal transportam informação do campo visual inferior " +
      "temporal. Por serem nasais, cruzam no quiasma óptico rumo ao trato contralateral. " +
      "Lesão isolada → escotoma inferior temporal no OD.",
    color: "#f0c040",
    crossesAtChiasm: true,
    angles: [30 * DEG, 60 * DEG],
    od: [{ type: "path", d: P.bottomRight }],
    oe: [],
  },

  // ── Superior temporal ─────────────────────────────────────────────────────
  // Temporal retina → nasal VF; superior retina → inferior VF
  // → inferior nasal of OD diagram = bottomLeft
  // Temporal → stays ipsilateral
  {
    id: "sup_temporal",
    label: "Fibras Sup. Temporais",
    retinalQuadrant: "Quadrante retinal superior temporal",
    description:
      "Fibras da retina superior temporal transportam informação do campo visual inferior " +
      "nasal. Por serem temporais, não cruzam no quiasma — permanecem ipsilaterais. " +
      "Lesão isolada → escotoma inferior nasal no OD.",
    color: "#ff8b94",
    crossesAtChiasm: false,
    angles: [120 * DEG, 150 * DEG],
    od: [{ type: "path", d: P.bottomLeft }],
    oe: [],
  },

  // ── Papillomacular bundle ─────────────────────────────────────────────────
  // Macular fibers enter the disc at the temporal pole (~180°)
  // → central scotoma OD (ipsilateral, pre-chiasmatic)
  {
    id: "macular",
    label: "Feixículo Papilomacular",
    retinalQuadrant: "Mácula / fóvea — visão central",
    description:
      "O feixículo papilomacular conecta a fóvea ao disco óptico pelo lado temporal. " +
      "É o feixe de maior densidade do nervo óptico — responsável pela acuidade de alta " +
      "resolução. Lesão → escotoma central denso ipsilateral (OD).",
    color: "#f0a500",
    crossesAtChiasm: false,
    angles: [165 * DEG, 195 * DEG],
    od: [{ type: "circle", cx: 45, cy: 45, r: 12 }],
    oe: [],
  },

  // ── Inferior temporal ────────────────────────────────────────────────────
  // Temporal retina → nasal VF; inferior retina → superior VF
  // → superior nasal of OD diagram = topLeft
  {
    id: "inf_temporal",
    label: "Fibras Inf. Temporais",
    retinalQuadrant: "Quadrante retinal inferior temporal",
    description:
      "Fibras da retina inferior temporal transportam informação do campo visual superior " +
      "nasal. Permanecem ipsilaterais pós-quiasma. " +
      "Lesão isolada → escotoma superior nasal no OD.",
    color: "#4ade80",
    crossesAtChiasm: false,
    angles: [210 * DEG, 240 * DEG],
    od: [{ type: "path", d: P.topLeft }],
    oe: [],
  },

  // ── Inferior nasal ───────────────────────────────────────────────────────
  // Nasal retina → temporal VF; inferior retina → superior VF
  // → superior temporal of OD diagram = topRight
  // Nasal → crosses at chiasm
  {
    id: "inf_nasal",
    label: "Fibras Inf. Nasais",
    retinalQuadrant: "Quadrante retinal inferior nasal",
    description:
      "Fibras da retina inferior nasal transportam informação do campo visual superior " +
      "temporal. Por serem nasais, cruzam no quiasma — afetam o hemisfério contralateral " +
      "após o cruzamento. Lesão isolada → escotoma superior temporal no OD.",
    color: "#54a0ff",
    crossesAtChiasm: true,
    angles: [300 * DEG, 330 * DEG],
    od: [{ type: "path", d: P.topRight }],
    oe: [],
  },
];

export const FIBER_REGION_MAP = new Map(FIBER_REGIONS.map((r) => [r.id, r]));
