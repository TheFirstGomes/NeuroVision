"use client";

/**
 * NeuroVision — 2D Anatomy Viewer
 *
 * Renders the reference anatomy illustration with interactive hotspots.
 * Each hotspot maps to a structure ID — clicking it fires the same
 * onStructureSelect callback used by the 3D viewer, so the sidebar
 * (Anatomy, Visual Field, Chat) works identically in both modes.
 */

import { useState } from "react";
import Image from "next/image";
import { STRUCTURE_MAP } from "@/lib/anatomy-data";

interface Props {
  selectedStructure: string | null;
  onStructureSelect: (id: string | null) => void;
}

// ── Hotspot positions (% from top-left of the image) ─────────────────────────
// Calibrated against the reference illustration (eye lower-right → cortex upper-left).

interface Hotspot {
  id: string;
  x: number;   // % from left
  y: number;   // % from top
}

const HOTSPOTS: Hotspot[] = [
  { id: "cornea",                    x: 85, y: 57 },
  { id: "retina",                    x: 74, y: 67 },
  { id: "macula",                    x: 70, y: 62 },
  { id: "disco_optico",              x: 63, y: 59 },
  { id: "nervo_optico",              x: 52, y: 52 },
  { id: "quiasma_optico",            x: 41, y: 45 },
  { id: "trato_optico",              x: 33, y: 37 },
  { id: "corpo_geniculado_lateral",  x: 24, y: 27 },
  { id: "radiacoes_opticas",         x: 18, y: 19 },
  { id: "cortex_visual",             x: 12, y: 11 },
];

// ── Component ─────────────────────────────────────────────────────────────────

export default function EyeViewer2D({ selectedStructure, onStructureSelect }: Props) {
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  const handleClick = (id: string) => {
    onStructureSelect(id === selectedStructure ? null : id);
  };

  return (
    <div className="w-full h-full relative flex items-center justify-center"
      style={{ background: "radial-gradient(ellipse at center, rgba(14,165,233,0.06) 0%, var(--bg-primary) 70%)" }}
    >
      {/* Background grid — matches 3D viewer */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          backgroundImage:
            "linear-gradient(rgba(78,205,196,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(78,205,196,0.03) 1px, transparent 1px)",
          backgroundSize: "40px 40px",
        }}
      />

      {/* Image + hotspot container — maintains aspect ratio */}
      <div className="relative" style={{ width: "min(100%, 560px)", aspectRatio: "1/1" }}>
        <Image
          src="/eye-anatomy-2d.png"
          alt="Anatomia do sistema visual — olho e via visual"
          fill
          style={{ objectFit: "contain" }}
          priority
          draggable={false}
        />

        {/* Hotspots */}
        {HOTSPOTS.map(({ id, x, y }) => {
          const meta    = STRUCTURE_MAP.get(id);
          if (!meta) return null;

          const selected = selectedStructure === id;
          const hovered  = hoveredId === id;
          const active   = selected || hovered;
          const color    = meta.color;

          return (
            <button
              key={id}
              onClick={() => handleClick(id)}
              onMouseEnter={() => setHoveredId(id)}
              onMouseLeave={() => setHoveredId(null)}
              style={{
                position: "absolute",
                left: `${x}%`,
                top:  `${y}%`,
                transform: "translate(-50%, -50%)",
                cursor: "pointer",
                background: "none",
                border: "none",
                padding: 0,
                zIndex: active ? 20 : 10,
              }}
              title={meta.label}
            >
              {/* Outer pulse ring (selected only) */}
              {selected && (
                <span
                  className="animate-ping"
                  style={{
                    position: "absolute",
                    inset: "-6px",
                    borderRadius: "50%",
                    background: color,
                    opacity: 0.25,
                  }}
                />
              )}

              {/* Dot */}
              <span
                style={{
                  display: "block",
                  width:  active ? "14px" : "10px",
                  height: active ? "14px" : "10px",
                  borderRadius: "50%",
                  background: color,
                  boxShadow: active
                    ? `0 0 0 2px rgba(5,13,26,0.9), 0 0 10px ${color}88`
                    : `0 0 0 1.5px rgba(5,13,26,0.8)`,
                  transition: "all 0.15s ease",
                  opacity: active ? 1 : 0.8,
                }}
              />

              {/* Label — always visible, positioned to avoid overlap */}
              <span
                style={{
                  position: "absolute",
                  top: "calc(100% + 5px)",
                  left: "50%",
                  transform: "translateX(-50%)",
                  whiteSpace: "nowrap",
                  fontSize: "9px",
                  fontWeight: 600,
                  letterSpacing: "0.04em",
                  color: active ? color : "rgba(255,255,255,0.55)",
                  textShadow: "0 1px 4px rgba(0,0,0,0.9)",
                  transition: "color 0.15s ease",
                  pointerEvents: "none",
                }}
              >
                {meta.label}
              </span>
            </button>
          );
        })}
      </div>

      {/* Hint */}
      {!selectedStructure && (
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 pointer-events-none">
          <p className="text-xs px-3 py-1.5 rounded-full"
            style={{ background: "rgba(5,13,26,0.7)", border: "1px solid var(--border)", color: "var(--text-muted)" }}>
            Clique em um ponto para explorar a estrutura
          </p>
        </div>
      )}

      <div className="absolute bottom-4 left-4 z-10">
        <p className="text-xs" style={{ color: "var(--text-muted)" }}>
          {HOTSPOTS.length} estruturas identificadas
        </p>
      </div>
    </div>
  );
}
