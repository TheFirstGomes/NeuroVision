"use client";

/**
 * Anatomy info panel — shown when user clicks a 3D structure.
 * Fetches live data from the backend anatomy endpoint.
 */

import { useEffect, useState } from "react";
import { X, Brain, Eye, AlertCircle, Zap } from "lucide-react";
import { fetchAnatomyStructure, AnatomyResponse } from "@/lib/api";

interface AnatomyPanelProps {
  structureId: string | null;
  onClose: () => void;
  onAskAbout: (question: string) => void;
}

export default function AnatomyPanel({ structureId, onClose, onAskAbout }: AnatomyPanelProps) {
  const [data, setData] = useState<AnatomyResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!structureId) {
      setData(null);
      return;
    }

    setLoading(true);
    setError(null);

    fetchAnatomyStructure(structureId)
      .then((result) => {
        setData(result);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [structureId]);

  if (!structureId) return null;

  return (
    <div
      className="h-full overflow-y-auto p-4 animate-fade-in-up"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Eye size={14} style={{ color: "var(--accent-teal)" }} />
          <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--accent-teal)" }}>
            Estrutura Selecionada
          </span>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded-lg transition-colors hover:bg-white/5"
          style={{ color: "var(--text-muted)" }}
        >
          <X size={14} />
        </button>
      </div>

      {loading && (
        <div className="flex items-center gap-2 py-4">
          <div className="flex gap-1">
            {[0, 1, 2].map((i) => (
              <div
                key={i}
                className={`loading-dot w-2 h-2 rounded-full`}
                style={{ background: "var(--accent-teal)" }}
              />
            ))}
          </div>
          <span className="text-sm" style={{ color: "var(--text-muted)" }}>
            Carregando...
          </span>
        </div>
      )}

      {error && (
        <div className="flex items-center gap-2 p-3 rounded-lg" style={{ background: "rgba(255,107,107,0.1)", border: "1px solid rgba(255,107,107,0.2)" }}>
          <AlertCircle size={14} style={{ color: "var(--accent-red)" }} />
          <span className="text-xs" style={{ color: "var(--accent-red)" }}>
            Backend offline — inicie o servidor
          </span>
        </div>
      )}

      {data && !loading && (
        <>
          {/* Structure name */}
          <div
            className="w-2 h-2 rounded-full inline-block mr-2"
            style={{ background: data.highlight_color }}
          />
          <h3 className="text-base font-bold inline" style={{ color: "var(--text-primary)" }}>
            {data.structure.name}
          </h3>

          {/* Description */}
          <p className="text-sm mt-3 leading-relaxed" style={{ color: "var(--text-secondary)" }}>
            {data.structure.description}
          </p>

          {/* Connections */}
          {data.structure.neurological_connections.length > 0 && (
            <div className="mt-3">
              <div className="flex items-center gap-1 mb-2">
                <Brain size={11} style={{ color: "var(--accent-teal)" }} />
                <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--accent-teal)" }}>
                  Conexões Neurológicas
                </span>
              </div>
              <div className="flex flex-wrap gap-1">
                {data.structure.neurological_connections.map((c) => (
                  <span key={c} className="structure-badge">
                    {c}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Pathologies */}
          {data.structure.associated_pathologies.length > 0 && (
            <div className="mt-3">
              <div className="flex items-center gap-1 mb-2">
                <AlertCircle size={11} style={{ color: "var(--accent-red)" }} />
                <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--accent-red)" }}>
                  Patologias Associadas
                </span>
              </div>
              <ul className="space-y-1">
                {data.structure.associated_pathologies.map((p) => (
                  <li
                    key={p}
                    className="text-xs pl-3 border-l-2 cursor-pointer transition-colors hover:opacity-80"
                    style={{
                      color: "var(--text-secondary)",
                      borderColor: "rgba(255,107,107,0.4)",
                    }}
                    onClick={() => onAskAbout(`O que é ${p} e qual sua relação com ${data.structure.name}?`)}
                  >
                    {p}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Clinical relevance */}
          {data.structure.clinical_relevance && (
            <div
              className="mt-3 p-3 rounded-lg text-xs leading-relaxed"
              style={{
                background: "rgba(78,205,196,0.06)",
                border: "1px solid rgba(78,205,196,0.15)",
                color: "var(--text-secondary)",
              }}
            >
              <span className="font-semibold" style={{ color: "var(--accent-teal)" }}>
                Relevância Clínica:{" "}
              </span>
              {data.structure.clinical_relevance}
            </div>
          )}

          {/* Ask button */}
          <button
            onClick={() =>
              onAskAbout(`Explique a importância clínica da ${data.structure.name} na neuro-oftalmologia`)
            }
            className="mt-3 w-full flex items-center justify-center gap-2 py-2 rounded-lg text-xs font-medium transition-all"
            style={{
              background: "rgba(78,205,196,0.12)",
              border: "1px solid rgba(78,205,196,0.25)",
              color: "var(--accent-teal)",
            }}
          >
            <Zap size={12} />
            Perguntar ao Tutor
          </button>
        </>
      )}
    </div>
  );
}
