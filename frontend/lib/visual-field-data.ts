/**
 * Visual field defect data for each anatomical structure.
 *
 * SVG coordinate system: viewBox "0 0 90 90", circle at cx=45 cy=45 r=42.
 * Diagram convention (patient perspective):
 *   Left side of diagram  = left visual space  (temporal OE / nasal OD)
 *   Right side of diagram = right visual space (temporal OD / nasal OE)
 *
 * All post-chiasmal defects shown for a RIGHT-sided lesion
 * (→ LEFT homonymous field loss) to illustrate the hemianopia sequence.
 */

export interface VFShape {
  type: "path" | "circle" | "ellipse";
  d?: string;       // path
  cx?: number;
  cy?: number;
  r?: number;       // circle
  rx?: number;
  ry?: number;      // ellipse (also uses cx/cy)
}

export interface VisualFieldData {
  structureId: string;
  defectName: string;
  defectNameEn: string;
  description: string;
  clinicalPearl: string;
  color: string;
  /** OD = right eye diagram (left = nasal, right = temporal) */
  od: VFShape[];
  /** OE = left eye diagram (left = temporal, right = nasal) */
  oe: VFShape[];
  /** Punch a 'macular sparing' hole at center after drawing oe/od */
  spareMacula?: boolean;
  /** Cornea / lens — reduces acuity but not a field defect */
  acuityOnly?: boolean;
}

// ── Pre-built SVG paths (cx=45, cy=45, r=42) ─────────────────────────────────

const P = {
  // Half fields
  leftHalf:    "M 45,3  A 42,42 0 0,0 45,87 L 45,45 Z",
  rightHalf:   "M 45,3  A 42,42 0 0,1 45,87 L 45,45 Z",
  topHalf:     "M 3,45  A 42,42 0 0,1 87,45 L 45,45 Z",
  bottomHalf:  "M 3,45  A 42,42 0 0,0 87,45 L 45,45 Z",
  // Quadrants
  topLeft:     "M 45,3  A 42,42 0 0,0 3,45  L 45,45 Z",
  topRight:    "M 45,3  A 42,42 0 0,1 87,45 L 45,45 Z",
  bottomLeft:  "M 3,45  A 42,42 0 0,0 45,87 L 45,45 Z",
  bottomRight: "M 87,45 A 42,42 0 0,0 45,87 L 45,45 Z",
} as const;

// ── Data ─────────────────────────────────────────────────────────────────────

export const VISUAL_FIELD_DATA: VisualFieldData[] = [
  // ── Córnea ────────────────────────────────────────────────────────────────
  {
    structureId: "cornea",
    defectName: "Redução de acuidade",
    defectNameEn: "Visual Acuity Reduction",
    description:
      "Patologias corneanas não produzem defeito de campo específico. Causam redução de acuidade por distorção óptica, representada aqui como escotoma central relativo.",
    clinicalPearl:
      "Ceratocone: distorção irregular, corrigível com lente rígida. Ceratite herpética: anestesia corneana é sinal patognomônico. Diferenciar de causas retinianas com teste do pinhole.",
    color: "#a8d8ea",
    acuityOnly: true,
    od: [{ type: "circle", cx: 45, cy: 45, r: 10 }],
    oe: [{ type: "circle", cx: 45, cy: 45, r: 10 }],
  },

  // ── Retina ────────────────────────────────────────────────────────────────
  {
    structureId: "retina",
    defectName: "Escotoma arqueado",
    defectNameEn: "Arcuate Scotoma",
    description:
      "Lesões na camada de fibras nervosas da retina causam defeitos arqueados que seguem o trajeto axonal. Exibido no quadrante superior temporal (OD) — padrão típico de neuropatia de fibra.",
    clinicalPearl:
      "Lesão inferior da retina → defeito SUPERIOR do campo (retinotopia invertida). RD proliferativa: múltiplos escotomas peri-centrais. OCT identifica a camada específica afetada: Camada de fibras nervosas (RNFL).",
    color: "#ff6b6b",
    od: [{ type: "path", d: P.topRight }],
    oe: [],
  },

  // ── Mácula ────────────────────────────────────────────────────────────────
  {
    structureId: "macula",
    defectName: "Escotoma central",
    defectNameEn: "Central Scotoma",
    description:
      "Lesão macular produz escotoma central ipsilateral com perda de visão de alta resolução, leitura e reconhecimento de faces. Campo periférico preservado.",
    clinicalPearl:
      "DMRI → escotoma central denso. Edema macular diabético → escotoma central relativo. Acuidade < 20/200 com campo periférico preservado é padrão macular clássico.",
    color: "#f0a500",
    od: [{ type: "circle", cx: 45, cy: 45, r: 13 }],
    oe: [],
  },

  // ── Disco Óptico ──────────────────────────────────────────────────────────
  {
    structureId: "disco_optico",
    defectName: "Defeito altitudinal superior",
    defectNameEn: "Superior Altitudinal Defect",
    description:
      "NOIA (Neuropatia Óptica Isquêmica Anterior) frequentemente afeta a metade inferior do disco → defeito altitudinal SUPERIOR. O campo se divide horizontalmente de modo preciso.",
    clinicalPearl:
      "NOIA arterítica (arterite de células gigantes): urgência! VSH + PCR elevados, biópsia imediata, corticoide EV. NOIA não-arterítica: fatores de risco cardiovascular, disco 'small & crowded'. Borda altitudinal precisa = lesão do disco.",
    color: "#f7dc6f",
    od: [{ type: "path", d: P.topHalf }],
    oe: [],
  },

  // ── Nervo Óptico ──────────────────────────────────────────────────────────
  {
    structureId: "nervo_optico",
    defectName: "Amaurose monocular",
    defectNameEn: "Monocular Amaurosis",
    description:
      "Lesão completa do nervo óptico produz perda total da visão ipsilateral. O olho contralateral e o reflexo consensual são preservados. Pupila com DPAR (Defeito Pupilar Aferente Relativo).",
    clinicalPearl:
      "Pupila de Marcus Gunn: swing flashlight test — pupila afetada DILATA quando a luz é movida para ela. Neurite óptica em EM: dor à movimentação ocular + escotoma central + Uhthoff (piora com calor). Meningioma do nervo: perda insidiosa sem dor.",
    color: "#4ecdc4",
    od: [{ type: "circle", cx: 45, cy: 45, r: 42 }],
    oe: [],
  },

  // ── Quiasma Óptico ────────────────────────────────────────────────────────
  {
    structureId: "quiasma_optico",
    defectName: "Hemianopsia bitemporal",
    defectNameEn: "Bitemporal Hemianopsia",
    description:
      "Compressão central do quiasma interrompe as fibras nasais cruzadas → perda dos campos temporais em ambos os olhos. As metades nasais (visão central) ficam preservadas.",
    clinicalPearl:
      "Adenoma hipofisário: causa mais comum. Sinais associados: cefaleia, galactorreia, amenorreia, acromegalia. Fenômeno de 'slip' ao volante é queixa típica. Juncional (ângulo quiasma-nervo): síndrome de Wilbrand.",
    color: "#ffe66d",
    od: [{ type: "path", d: P.rightHalf }],  // OD temporal = lado direito
    oe: [{ type: "path", d: P.leftHalf }],   // OE temporal = lado esquerdo
  },

  // ── Trato Óptico ──────────────────────────────────────────────────────────
  {
    structureId: "trato_optico",
    defectName: "Hemianopsia homônima incongruente",
    defectNameEn: "Incongruent Homonymous Hemianopsia",
    description:
      "Lesão do trato óptico direito → perda do campo visual ESQUERDO em ambos os olhos. Incongruente: os padrões entre OD e OE são assimétricos.",
    clinicalPearl:
      "Incongruência = diferença entre os dois campos → lesão mais ANTERIOR (trato). Congruência perfeita = lesão mais POSTERIOR (córtex). DPAR ipsilateral à lesão pode ocorrer no trato (fibras pupilares percorrem o trato até o mesencéfalo).",
    color: "#a8e6cf",
    od: [{ type: "path", d: P.leftHalf }],
    oe: [{ type: "path", d: P.leftHalf }],
  },

  // ── Corpo Geniculado Lateral ──────────────────────────────────────────────
  {
    structureId: "corpo_geniculado_lateral",
    defectName: "Hemianopsia homônima",
    defectNameEn: "Homonymous Hemianopsia",
    description:
      "Lesão do CGL direito → hemianopsia homônima esquerda. Padrão semelhante ao trato, porém sem DPAR (fibras pupilares divergem antes do CGL) e sem incongruência.",
    clinicalPearl:
      "CGL: única estação talâmica da via visual. Lesões vasculares são as mais comuns (ramos talâmicos da ACP). Duplo suprimento vascular (ACP + ACP anterior) pode gerar preservação de setor horizontal — padrão 'em cunha' patognomônico do CGL.",
    color: "#ff8b94",
    od: [{ type: "path", d: P.leftHalf }],
    oe: [{ type: "path", d: P.leftHalf }],
  },

  // ── Radiações Ópticas ────────────────────────────────────────────────────
  {
    structureId: "radiacoes_opticas",
    defectName: "Quadrantanopsia superior esquerda",
    defectNameEn: "Superior Left Quadrantanopsia — 'Pie in the Sky'",
    description:
      "Alça de Meyer (fibras inferiores no lobo temporal) → lesão → quadrantanopsia SUPERIOR contralateral. Padrão conhecido como 'pie in the sky'.",
    clinicalPearl:
      "'Pie in the sky' = lesão temporal. 'Pie in the floor' (quadrantanopsia inferior) = lesão parietal (fibras superiores). Epilepsia do lobo temporal frequentemente associada. Lobectomia temporal cirúrgica pode causar este defeito.",
    color: "#dda0dd",
    od: [{ type: "path", d: P.topLeft }],
    oe: [{ type: "path", d: P.topLeft }],
  },

  // ── Córtex Visual ─────────────────────────────────────────────────────────
  {
    structureId: "cortex_visual",
    defectName: "Hemianopsia + poupamento macular",
    defectNameEn: "Homonymous Hemianopsia with Macular Sparing",
    description:
      "AVC occipital direito → hemianopsia esquerda. O polo occipital (representação macular) é poupado por duplo suprimento vascular (ACP + ramos da ACM).",
    clinicalPearl:
      "Poupamento macular = assinatura de lesão CORTICAL. Migrânea com aura: escotoma cintilante que se expande centrifugamente do ponto de fixação (onda de depressão cortical alastrada). Agnosia visual, prosopagnosia e achromatopsia ocorrem em lesões bilaterais.",
    color: "#98ddca",
    spareMacula: true,
    od: [{ type: "path", d: P.leftHalf }],
    oe: [{ type: "path", d: P.leftHalf }],
  },
];

export const VISUAL_FIELD_MAP = new Map(
  VISUAL_FIELD_DATA.map((d) => [d.structureId, d])
);
