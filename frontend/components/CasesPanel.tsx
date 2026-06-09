"use client";

/**
 * Clinical Cases Panel — NeuroVision
 *
 * Resident-level case-based learning module.
 * Left: case list. Right: case detail with patient info, questions (reveal-on-click),
 * teaching point, and links to the 3D viewer and visual field simulator.
 */

import { useState, useEffect, useCallback } from "react";
import {
  X, BookOpen, ChevronRight, User, Stethoscope, HelpCircle,
  CheckCircle, Eye, Lightbulb, Loader2, AlertTriangle, Activity,
} from "lucide-react";
import { fetchCases, fetchCase, type CaseListItem, type ClinicalCase, type CaseQuestion } from "@/lib/api";

const DIFFICULTY_LABEL = ["", "Básico", "Intermediário", "Avançado"];
const DIFFICULTY_COLOR = ["", "#4ade80", "#ffe66d", "#ff8b94"];

const CATEGORY_COLOR: Record<string, string> = {
  "Nervo Óptico":  "#f0c040",   // gold — conduction
  "Quiasma":       "#ff9f43",   // orange — decussation
  "Disco Óptico":  "#f7dc6f",   // light yellow — optic disc
  "Retina":        "#ff6b6b",   // red — origin
  "Córtex Visual": "#74d7f7",   // cyan — processing
  "Mácula":        "#f0a500",   // amber
};

interface Props {
  onClose: () => void;
  onStructureHighlight: (id: string) => void;
}

// ── Question card ─────────────────────────────────────────────────────────────

function QuestionCard({ q, index }: { q: CaseQuestion; index: number }) {
  const [revealed, setRevealed] = useState(false);

  return (
    <div
      className="rounded-xl overflow-hidden"
      style={{ border: "1px solid rgba(78,205,196,0.15)" }}
    >
      {/* Question */}
      <div className="px-4 py-3" style={{ background: "rgba(13,31,53,0.6)" }}>
        <div className="flex items-start gap-2">
          <span
            className="text-xs font-bold shrink-0 mt-0.5"
            style={{ color: "var(--accent-teal)" }}
          >
            Q{index + 1}
          </span>
          <p className="text-sm" style={{ color: "var(--text-primary)" }}>{q.question}</p>
        </div>
      </div>

      {/* Answer toggle */}
      {!revealed ? (
        <button
          className="w-full px-4 py-2.5 flex items-center gap-2 text-xs font-medium transition-all hover:bg-white/5"
          style={{
            background: "rgba(78,205,196,0.06)",
            borderTop: "1px solid rgba(78,205,196,0.12)",
            color: "var(--accent-teal)",
          }}
          onClick={() => setRevealed(true)}
        >
          <HelpCircle size={12} />
          Revelar resposta
        </button>
      ) : (
        <div style={{ borderTop: "1px solid rgba(78,205,196,0.12)" }}>
          {/* Answer */}
          <div
            className="px-4 py-3 flex items-start gap-2"
            style={{ background: "rgba(74,222,128,0.06)" }}
          >
            <CheckCircle size={13} style={{ color: "#4ade80", flexShrink: 0, marginTop: "2px" }} />
            <p className="text-sm font-medium" style={{ color: "#4ade80" }}>{q.answer}</p>
          </div>
          {/* Explanation */}
          <div
            className="px-4 py-3"
            style={{ background: "rgba(13,31,53,0.4)" }}
          >
            <p className="text-xs leading-relaxed" style={{ color: "var(--text-secondary)" }}>
              {q.explanation}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Case detail ───────────────────────────────────────────────────────────────

function CaseDetail({
  caseId,
  onStructureHighlight,
  onClose,
}: {
  caseId: string;
  onStructureHighlight: (id: string) => void;
  onClose: () => void;
}) {
  const [data, setData] = useState<ClinicalCase | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    setData(null);
    fetchCase(caseId)
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [caseId]);

  if (loading)
    return (
      <div className="flex-1 flex items-center justify-center gap-3">
        <Loader2 size={18} className="animate-spin" style={{ color: "var(--accent-teal)" }} />
        <span className="text-sm" style={{ color: "var(--text-muted)" }}>Carregando caso...</span>
      </div>
    );

  if (error || !data)
    return (
      <div className="flex-1 flex items-center justify-center p-6">
        <div className="flex items-start gap-3 p-4 rounded-xl" style={{ background: "rgba(255,107,107,0.08)", border: "1px solid rgba(255,107,107,0.2)" }}>
          <AlertTriangle size={16} style={{ color: "var(--accent-red)" }} className="shrink-0" />
          <p className="text-sm" style={{ color: "var(--accent-red)" }}>{error || "Erro ao carregar caso"}</p>
        </div>
      </div>
    );

  const catColor = CATEGORY_COLOR[data.category] ?? "var(--accent-teal)";

  return (
    <div className="flex-1 overflow-y-auto p-5 space-y-4 animate-fade-in-up">
      {/* Title */}
      <div>
        <div className="flex items-center gap-2 mb-1.5">
          <span
            className="text-xs px-2 py-0.5 rounded-full font-medium"
            style={{ background: `${catColor}18`, border: `1px solid ${catColor}40`, color: catColor }}
          >
            {data.category}
          </span>
          <span
            className="text-xs px-2 py-0.5 rounded-full"
            style={{
              background: `${DIFFICULTY_COLOR[data.difficulty]}15`,
              border: `1px solid ${DIFFICULTY_COLOR[data.difficulty]}35`,
              color: DIFFICULTY_COLOR[data.difficulty],
            }}
          >
            {DIFFICULTY_LABEL[data.difficulty]}
          </span>
        </div>
        <h3 className="text-sm font-semibold leading-snug" style={{ color: "var(--text-primary)" }}>
          {data.title}
        </h3>
      </div>

      {/* Patient card */}
      <div
        className="rounded-xl p-4 space-y-3"
        style={{ background: "rgba(13,31,53,0.7)", border: "1px solid rgba(78,205,196,0.12)" }}
      >
        <div className="flex items-center gap-2">
          <User size={13} style={{ color: "var(--accent-teal)" }} />
          <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--accent-teal)" }}>
            Apresentação
          </span>
          <span className="text-xs" style={{ color: "var(--text-muted)" }}>
            — {data.patient.age} anos, {data.patient.sex === "F" ? "feminino" : "masculino"}
          </span>
        </div>

        <div className="space-y-2">
          <div>
            <p className="text-xs font-medium mb-0.5" style={{ color: "var(--text-muted)" }}>Queixa principal</p>
            <p className="text-xs leading-relaxed" style={{ color: "var(--text-secondary)" }}>
              {data.patient.chief_complaint}
            </p>
          </div>
          <div>
            <p className="text-xs font-medium mb-0.5" style={{ color: "var(--text-muted)" }}>História</p>
            <p className="text-xs leading-relaxed" style={{ color: "var(--text-secondary)" }}>
              {data.patient.history}
            </p>
          </div>
          <div>
            <p className="text-xs font-medium mb-0.5" style={{ color: "var(--text-muted)" }}>
              <Stethoscope size={10} className="inline mr-1" />
              Exame
            </p>
            <p className="text-xs leading-relaxed" style={{ color: "var(--text-secondary)" }}>
              {data.patient.examination}
            </p>
          </div>
        </div>
      </div>

      {/* Questions */}
      <div>
        <p className="text-xs font-semibold uppercase tracking-wider mb-2.5" style={{ color: "var(--text-muted)" }}>
          Questões
        </p>
        <div className="space-y-3">
          {data.questions.map((q, i) => (
            <QuestionCard key={i} q={q} index={i} />
          ))}
        </div>
      </div>

      {/* Teaching point */}
      <div
        className="rounded-xl p-4 flex items-start gap-3"
        style={{ background: "rgba(255,230,109,0.06)", border: "1px solid rgba(255,230,109,0.2)" }}
      >
        <Lightbulb size={14} style={{ color: "#ffe66d", flexShrink: 0, marginTop: "1px" }} />
        <div>
          <p className="text-xs font-semibold mb-1" style={{ color: "#ffe66d" }}>Ponto de Ensino</p>
          <p className="text-xs leading-relaxed" style={{ color: "var(--text-secondary)" }}>
            {data.teaching_point}
          </p>
        </div>
      </div>

      {/* Link to 3D viewer */}
      <div className="flex gap-2 flex-wrap">
        <button
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all glass-hover"
          style={{
            background: `${catColor}10`,
            border: `1px solid ${catColor}30`,
            color: catColor,
          }}
          onClick={() => {
            onStructureHighlight(data.related_structure);
            onClose();
          }}
        >
          <Eye size={11} />
          Ver no modelo 3D
        </button>
        <button
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all glass-hover"
          style={{
            background: "rgba(78,205,196,0.08)",
            border: "1px solid rgba(78,205,196,0.2)",
            color: "var(--accent-teal)",
          }}
          onClick={() => {
            onStructureHighlight(data.visual_field_structure);
            onClose();
          }}
        >
          <Activity size={11} />
          Ver campo visual
        </button>
      </div>
    </div>
  );
}

// ── Main panel ────────────────────────────────────────────────────────────────

export default function CasesPanel({ onClose, onStructureHighlight }: Props) {
  const [cases, setCases] = useState<CaseListItem[]>([]);
  const [loadingList, setLoadingList] = useState(true);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  useEffect(() => {
    fetchCases()
      .then((list) => {
        setCases(list);
        if (list.length > 0) setSelectedId(list[0].id);
      })
      .catch(() => setCases([]))
      .finally(() => setLoadingList(false));
  }, []);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: "rgba(0,0,0,0.65)", backdropFilter: "blur(4px)" }}
    >
      <div
        className="glass rounded-2xl w-full flex flex-col overflow-hidden"
        style={{
          maxWidth: "860px",
          maxHeight: "90vh",
          border: "1px solid rgba(78,205,196,0.25)",
        }}
      >
        {/* Header */}
        <div
          className="flex items-center justify-between px-5 py-4 border-b shrink-0"
          style={{ borderColor: "var(--border)" }}
        >
          <div className="flex items-center gap-2">
            <BookOpen size={16} style={{ color: "var(--accent-teal)" }} />
            <h2 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
              Casos Clínicos
            </h2>
            <span
              className="text-xs px-2 py-0.5 rounded-full"
              style={{
                background: "rgba(78,205,196,0.12)",
                border: "1px solid rgba(78,205,196,0.25)",
                color: "var(--accent-teal)",
              }}
            >
              {cases.length} casos
            </span>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-white/5 transition-colors"
            style={{ color: "var(--text-muted)" }}
          >
            <X size={15} />
          </button>
        </div>

        {/* Body */}
        <div className="flex flex-1 overflow-hidden">
          {/* Sidebar */}
          <div
            className="w-60 shrink-0 overflow-y-auto py-2"
            style={{ borderRight: "1px solid var(--border)", background: "rgba(5,13,26,0.5)" }}
          >
            {loadingList ? (
              <div className="flex justify-center py-8">
                <Loader2 size={16} className="animate-spin" style={{ color: "var(--accent-teal)" }} />
              </div>
            ) : (
              cases.map((c) => {
                const catColor = CATEGORY_COLOR[c.category] ?? "var(--accent-teal)";
                const isActive = c.id === selectedId;
                return (
                  <button
                    key={c.id}
                    className="w-full px-3 py-3 text-left transition-all"
                    style={{
                      background: isActive ? `${catColor}12` : "transparent",
                      borderLeft: isActive ? `2px solid ${catColor}` : "2px solid transparent",
                    }}
                    onClick={() => setSelectedId(c.id)}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <p
                        className="text-xs font-medium leading-snug"
                        style={{ color: isActive ? "var(--text-primary)" : "var(--text-secondary)" }}
                      >
                        {c.title}
                      </p>
                      <ChevronRight
                        size={11}
                        style={{ color: isActive ? catColor : "var(--text-muted)", flexShrink: 0, marginTop: "2px" }}
                      />
                    </div>
                    <div className="flex items-center gap-1.5 mt-1.5">
                      <span
                        className="text-xs px-1.5 py-0.5 rounded"
                        style={{ background: `${catColor}15`, color: catColor, fontSize: "10px" }}
                      >
                        {c.category}
                      </span>
                      <span
                        className="text-xs"
                        style={{ color: DIFFICULTY_COLOR[c.difficulty], fontSize: "10px" }}
                      >
                        {"●".repeat(c.difficulty)}
                      </span>
                    </div>
                  </button>
                );
              })
            )}
          </div>

          {/* Detail */}
          <div className="flex flex-1 overflow-hidden">
            {selectedId ? (
              <CaseDetail
                key={selectedId}
                caseId={selectedId}
                onStructureHighlight={onStructureHighlight}
                onClose={onClose}
              />
            ) : (
              <div className="flex-1 flex items-center justify-center">
                <p className="text-sm" style={{ color: "var(--text-muted)" }}>
                  Selecione um caso
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
