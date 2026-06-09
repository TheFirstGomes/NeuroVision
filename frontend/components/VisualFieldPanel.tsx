"use client";

/**
 * Visual Field Defect Simulator — sidebar panel variant.
 *
 * Renders two SVG perimetry diagrams (OE | OD) showing the characteristic
 * field loss for the selected anatomical structure.
 *
 * When a fiber region is also selected (via click in the 3D nerve fiber bundle),
 * shows an additional "Fibra Selecionada" section with the quadrant-specific
 * patch and retinotopic mapping explanation.
 */

import { useEffect, useState } from "react";
import { Activity } from "lucide-react";
import { VISUAL_FIELD_MAP, type VFShape } from "@/lib/visual-field-data";
import { FIBER_REGION_MAP } from "@/lib/fiber-region-data";

interface Props {
  structureId: string | null;
  fiberRegion?: string | null;
}

// ── Shape renderer ────────────────────────────────────────────────────────────

function renderShape(shape: VFShape, color: string, clipId: string, idx: number) {
  const common = { fill: color, opacity: 0.74, clipPath: `url(#${clipId})` };
  if (shape.type === "path" && shape.d)
    return <path key={idx} d={shape.d} {...common} />;
  if (shape.type === "circle" && shape.cx !== undefined)
    return <circle key={idx} cx={shape.cx} cy={shape.cy} r={shape.r} {...common} />;
  if (shape.type === "ellipse" && shape.cx !== undefined)
    return <ellipse key={idx} cx={shape.cx} cy={shape.cy} rx={shape.rx} ry={shape.ry} {...common} />;
  return null;
}

// ── Single eye diagram ────────────────────────────────────────────────────────

function EyeDiagram({
  shapes, label, id, color, spareMacula, acuityOnly, isOD,
}: {
  shapes: VFShape[]; label: string; id: string; color: string;
  spareMacula?: boolean; acuityOnly?: boolean; isOD?: boolean;
}) {
  const hasDefect = shapes.length > 0;
  return (
    <div className="flex flex-col items-center gap-1.5">
      <svg width={86} height={86} viewBox="0 0 90 90">
        <defs>
          <clipPath id={id}><circle cx="45" cy="45" r="42" /></clipPath>
        </defs>
        <circle cx="45" cy="45" r="42"
          fill="rgba(4,11,22,0.95)"
          stroke={hasDefect ? `${color}60` : "rgba(255,255,255,0.1)"}
          strokeWidth={hasDefect ? "1.5" : "1"}
        />
        <line x1="45" y1="4" x2="45" y2="86" stroke="rgba(255,255,255,0.08)" strokeWidth="0.6" />
        <line x1="4" y1="45" x2="86" y2="45" stroke="rgba(255,255,255,0.08)" strokeWidth="0.6" />
        <circle cx="45" cy="45" r="14" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="0.5" />
        <circle cx="45" cy="45" r="28" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="0.5" />
        {shapes.map((s, i) => renderShape(s, color, id, i))}
        {spareMacula && hasDefect && (
          <circle cx="45" cy="45" r="11" fill="rgba(4,11,22,0.95)" />
        )}
        {acuityOnly && hasDefect && (
          <circle cx="45" cy="45" r="10" fill={color} opacity="0.18" clipPath={`url(#${id})`} />
        )}
        <circle cx={isOD ? 58 : 32} cy="45" r="4"
          fill="none" stroke="rgba(255,255,255,0.13)" strokeWidth="0.7" strokeDasharray="2 2"
        />
        <circle cx="45" cy="45" r="2.2" fill="rgba(255,255,255,0.55)" />
        <circle cx="45" cy="45" r="0.8" fill="rgba(255,255,255,0.9)" />
      </svg>
      <span className="text-xs font-semibold tracking-widest" style={{ color: "var(--text-muted)" }}>
        {label}
      </span>
    </div>
  );
}

// ── Fiber region section ──────────────────────────────────────────────────────

function FiberRegionSection({ regionId }: { regionId: string }) {
  const region = FIBER_REGION_MAP.get(regionId);
  if (!region) return null;
  const clipId = `vf-fr-${regionId}`;

  return (
    <div
      className="rounded-xl p-3 space-y-2.5"
      style={{ background: `${region.color}08`, border: `1px solid ${region.color}35` }}
    >
      {/* Header */}
      <div className="flex items-center gap-2 flex-wrap">
        <div className="w-2 h-2 rounded-full shrink-0" style={{ background: region.color }} />
        <span className="text-xs font-semibold" style={{ color: region.color }}>
          {region.label}
        </span>
        {region.crossesAtChiasm && (
          <span
            className="text-xs px-1.5 py-0.5 rounded"
            style={{ background: "#ff9f4318", border: "1px solid #ff9f4330", color: "#ff9f43", fontSize: "10px" }}
          >
            ↕ cruza no quiasma
          </span>
        )}
      </div>

      <p className="text-xs" style={{ color: "var(--text-muted)" }}>{region.retinalQuadrant}</p>

      {/* Mini OD diagram + description side by side */}
      <div className="flex gap-3 items-start">
        <div className="flex flex-col items-center gap-1 shrink-0">
          <svg width={58} height={58} viewBox="0 0 90 90">
            <defs><clipPath id={clipId}><circle cx="45" cy="45" r="42" /></clipPath></defs>
            <circle cx="45" cy="45" r="42" fill="rgba(4,11,22,0.95)" stroke={`${region.color}45`} strokeWidth="1.5" />
            <line x1="45" y1="4" x2="45" y2="86" stroke="rgba(255,255,255,0.08)" strokeWidth="0.6" />
            <line x1="4" y1="45" x2="86" y2="45" stroke="rgba(255,255,255,0.08)" strokeWidth="0.6" />
            <circle cx="45" cy="45" r="14" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="0.5" />
            {region.od.map((s, i) => {
              const common = { fill: region.color, opacity: 0.8 as number, clipPath: `url(#${clipId})` };
              if (s.type === "path" && s.d) return <path key={i} d={s.d} {...common} />;
              if (s.type === "circle") return <circle key={i} cx={s.cx} cy={s.cy} r={s.r} {...common} />;
              return null;
            })}
            <circle cx="45" cy="45" r="2.2" fill="rgba(255,255,255,0.55)" />
          </svg>
          <span style={{ fontSize: "9px", color: "var(--text-muted)" }}>OD — lesão isolada</span>
        </div>

        <p className="text-xs leading-relaxed flex-1 pt-0.5" style={{ color: "var(--text-secondary)" }}>
          {region.description}
        </p>
      </div>
    </div>
  );
}

// ── Panel ─────────────────────────────────────────────────────────────────────

export default function VisualFieldPanel({ structureId, fiberRegion }: Props) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    setVisible(false);
    const t = setTimeout(() => setVisible(true), 40);
    return () => clearTimeout(t);
  }, [structureId, fiberRegion]);

  // Show fiber-only view when no structure is selected but a fiber region is
  if (!structureId && fiberRegion) {
    return (
      <div
        className="h-full overflow-y-auto p-4 space-y-4"
        style={{ opacity: visible ? 1 : 0, transition: "opacity 0.2s ease" }}
      >
        <div className="flex items-center gap-2 mb-1">
          <Activity size={13} style={{ color: "var(--accent-teal)" }} />
          <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--accent-teal)" }}>
            Fibra Selecionada
          </span>
        </div>
        <FiberRegionSection regionId={fiberRegion} />
        <div
          className="rounded-xl p-3 text-xs leading-relaxed"
          style={{ background: "rgba(13,31,53,0.6)", border: "1px solid rgba(78,205,196,0.1)", color: "var(--text-secondary)" }}
        >
          Defeito representado para lesão isolada desta região no nervo óptico direito (pré-quiasmático → OD afetado).
          Selecione uma estrutura no modelo 3D para ver o campo visual completo da patologia.
        </div>
      </div>
    );
  }

  if (!structureId) return (
    <div className="flex flex-col items-center justify-center h-full gap-3 p-6 text-center">
      <Activity size={32} style={{ color: "var(--text-muted)", opacity: 0.3 }} />
      <p className="text-sm" style={{ color: "var(--text-muted)" }}>
        Selecione uma estrutura no modelo 3D para ver o defeito de campo visual correspondente
      </p>
    </div>
  );

  const data = VISUAL_FIELD_MAP.get(structureId);
  if (!data) return (
    <div className="flex flex-col items-center justify-center h-full p-6">
      <p className="text-sm" style={{ color: "var(--text-muted)" }}>
        Sem dados de campo visual para esta estrutura
      </p>
    </div>
  );

  return (
    <div
      className="h-full overflow-y-auto p-4 space-y-4"
      style={{ opacity: visible ? 1 : 0, transition: "opacity 0.2s ease" }}
    >
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <Activity size={13} style={{ color: data.color }} />
          <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: data.color }}>
            Campo Visual
          </span>
        </div>
        <p className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
          {data.defectName}
        </p>
        <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
          {data.defectNameEn}
        </p>
      </div>

      {/* Diagrams */}
      <div
        className="flex items-end justify-center gap-6 py-3 rounded-xl"
        style={{ background: "rgba(4,11,22,0.5)", border: `1px solid ${data.color}25` }}
      >
        <EyeDiagram
          shapes={data.oe} label="OE" id={`vf-oe-${structureId}`}
          color={data.color} spareMacula={data.spareMacula} acuityOnly={data.acuityOnly} isOD={false}
        />
        <div style={{ width: "1px", height: "50px", background: `${data.color}20` }} />
        <EyeDiagram
          shapes={data.od} label="OD" id={`vf-od-${structureId}`}
          color={data.color} spareMacula={data.spareMacula} acuityOnly={data.acuityOnly} isOD={true}
        />
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-4 text-xs" style={{ color: "var(--text-muted)" }}>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-full" style={{ background: data.color, opacity: 0.7 }} />
          <span>Área afetada</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-full" style={{ background: "rgba(255,255,255,0.15)" }} />
          <span>Campo preservado</span>
        </div>
      </div>

      {/* Description */}
      <div
        className="rounded-xl p-3 text-xs leading-relaxed"
        style={{ background: "rgba(13,31,53,0.6)", border: "1px solid rgba(78,205,196,0.1)", color: "var(--text-secondary)" }}
      >
        {data.description}
      </div>

      {/* Clinical pearl */}
      <div
        className="rounded-xl p-3 flex items-start gap-2 text-xs leading-relaxed"
        style={{ background: `${data.color}0e`, border: `1px solid ${data.color}28`, color: "var(--text-muted)" }}
      >
        <span style={{ color: data.color, flexShrink: 0 }}>⚡</span>
        <span>{data.clinicalPearl}</span>
      </div>

      {/* Fiber region annotation — shown when a fiber was clicked in 3D */}
      {fiberRegion && (
        <div className="space-y-2">
          <p
            className="text-xs font-semibold uppercase tracking-wider"
            style={{ color: "var(--text-muted)" }}
          >
            Fibra selecionada no nervo óptico
          </p>
          <FiberRegionSection regionId={fiberRegion} />
        </div>
      )}
    </div>
  );
}
