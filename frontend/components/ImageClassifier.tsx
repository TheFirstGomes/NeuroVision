"use client";

/**
 * Fundoscopy Image Classifier Panel
 * Upload a retinal image → get classification + RAG explanation
 */

import { useState, useCallback, useRef } from "react";
import {
  Upload, X, Loader2, AlertTriangle, CheckCircle,
  Brain, Eye, Zap, ChevronDown, ChevronUp, ScanEye,
} from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ClassificationResult {
  condition: string;
  condition_en: string;
  confidence: number;
  severity: string;
  neurological_flag: boolean;
  neurological_note: string;
  features_detected: string[];
  explanation: string;
  related_structures: string[];
  disclaimer: string;
  classifier_method?: string;
}

interface ImageClassifierProps {
  onClose: () => void;
  onStructureHighlight: (id: string) => void;
}

const SEVERITY_COLORS: Record<string, string> = {
  normal:     "#4ade80",
  leve:       "#ffe66d",
  moderado:   "#f0a500",
  grave:      "#ff6b6b",
  suspeito:   "#dda0dd",
};

const SAMPLE_IMAGES = [
  { label: "Retina Normal",            hint: "fundo_normal.jpg" },
  { label: "Retinopatia Diabética",    hint: "retinopatia.jpg"  },
  { label: "Glaucoma",                 hint: "glaucoma.jpg"     },
  { label: "DMRI",                     hint: "dmri.jpg"         },
];

export default function ImageClassifier({ onClose, onStructureHighlight }: ImageClassifierProps) {
  const [preview, setPreview]     = useState<string | null>(null);
  const [file, setFile]           = useState<File | null>(null);
  const [loading, setLoading]     = useState(false);
  const [result, setResult]       = useState<ClassificationResult | null>(null);
  const [error, setError]         = useState<string | null>(null);
  const [dragOver, setDragOver]   = useState(false);
  const [showExplan, setShowExplan] = useState(true);
  const inputRef = useRef<HTMLInputElement>(null);

  const loadFile = useCallback((f: File) => {
    if (!f.type.startsWith("image/")) {
      setError("Envie uma imagem JPEG ou PNG.");
      return;
    }
    setFile(f);
    setResult(null);
    setError(null);
    const reader = new FileReader();
    reader.onload = (e) => setPreview(e.target?.result as string);
    reader.readAsDataURL(f);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f) loadFile(f);
  }, [loadFile]);

  const handleClassify = useCallback(async () => {
    if (!file) return;
    setLoading(true);
    setError(null);

    const form = new FormData();
    form.append("file", file);

    try {
      const res = await fetch(`${API_URL}/classify`, { method: "POST", body: form });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Erro na classificação");
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Falha na conexão com o backend.");
    } finally {
      setLoading(false);
    }
  }, [file]);

  const severityColor = result ? SEVERITY_COLORS[result.severity] ?? "#8bb8d4" : "";

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: "rgba(0,0,0,0.65)", backdropFilter: "blur(4px)" }}
    >
      <div
        className="glass rounded-2xl w-full flex flex-col"
        style={{
          maxWidth: "760px",
          maxHeight: "90vh",
          border: "1px solid rgba(78,205,196,0.25)",
        }}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b shrink-0" style={{ borderColor: "var(--border)" }}>
          <div className="flex items-center gap-2">
            <ScanEye size={16} style={{ color: "var(--accent-teal)" }} />
            <h2 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
              Análise de Fundoscopia
            </h2>
            <span className="text-xs px-2 py-0.5 rounded-full" style={{ background: "rgba(255,230,109,0.12)", border: "1px solid rgba(255,230,109,0.25)", color: "#ffe66d" }}>
              Educacional
            </span>
          </div>
          <button onClick={onClose} className="p-1 rounded-lg hover:bg-white/5 transition-colors" style={{ color: "var(--text-muted)" }}>
            <X size={15} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto">
          <div className="flex flex-col md:flex-row gap-0 h-full">

            {/* Left: upload */}
            <div className="p-5 flex flex-col gap-4 md:w-72 shrink-0 border-b md:border-b-0 md:border-r" style={{ borderColor: "var(--border)" }}>
              {/* Drop zone */}
              <div
                className="relative rounded-xl border-2 border-dashed overflow-hidden cursor-pointer transition-all"
                style={{
                  borderColor: dragOver ? "var(--accent-teal)" : preview ? "rgba(78,205,196,0.4)" : "var(--border)",
                  background: dragOver ? "rgba(78,205,196,0.06)" : "rgba(13,31,53,0.5)",
                  aspectRatio: "1 / 1",
                }}
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleDrop}
                onClick={() => !preview && inputRef.current?.click()}
              >
                <input ref={inputRef} type="file" accept="image/*" className="hidden" onChange={(e) => e.target.files?.[0] && loadFile(e.target.files[0])} />

                {preview ? (
                  <>
                    <img src={preview} alt="Fundoscopia" className="w-full h-full object-cover" />
                    <button
                      className="absolute top-2 right-2 p-1 rounded-full"
                      style={{ background: "rgba(0,0,0,0.6)" }}
                      onClick={(e) => { e.stopPropagation(); setPreview(null); setFile(null); setResult(null); }}
                    >
                      <X size={12} style={{ color: "white" }} />
                    </button>
                  </>
                ) : (
                  <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 p-4">
                    <Upload size={28} style={{ color: "var(--text-muted)" }} />
                    <p className="text-xs text-center" style={{ color: "var(--text-secondary)" }}>
                      Arraste uma imagem de fundoscopia ou clique para selecionar
                    </p>
                    <p className="text-xs" style={{ color: "var(--text-muted)" }}>JPEG · PNG · máx 20MB</p>
                  </div>
                )}
              </div>

              {/* Classify button */}
              <button
                onClick={handleClassify}
                disabled={!file || loading}
                className="w-full py-2.5 rounded-xl text-sm font-semibold transition-all flex items-center justify-center gap-2"
                style={{
                  background: file && !loading ? "linear-gradient(135deg, rgba(78,205,196,0.25), rgba(14,165,233,0.2))" : "rgba(255,255,255,0.04)",
                  border: `1px solid ${file && !loading ? "rgba(78,205,196,0.5)" : "var(--border)"}`,
                  color: file && !loading ? "var(--accent-teal)" : "var(--text-muted)",
                  cursor: file && !loading ? "pointer" : "not-allowed",
                }}
              >
                {loading ? <><Loader2 size={15} className="animate-spin" /> Analisando...</> : <><Zap size={15} /> Analisar Imagem</>}
              </button>

              {/* Sample hint */}
              <div>
                <p className="text-xs mb-2" style={{ color: "var(--text-muted)" }}>
                  Tipos de imagem suportados:
                </p>
                <div className="flex flex-wrap gap-1">
                  {SAMPLE_IMAGES.map((s) => (
                    <span key={s.label} className="structure-badge text-xs">{s.label}</span>
                  ))}
                </div>
              </div>
            </div>

            {/* Right: result */}
            <div className="flex-1 p-5 overflow-y-auto">
              {!result && !error && !loading && (
                <div className="h-full flex flex-col items-center justify-center gap-3 text-center">
                  <Eye size={40} style={{ color: "var(--text-muted)", opacity: 0.4 }} />
                  <p className="text-sm" style={{ color: "var(--text-muted)" }}>
                    Faça upload de uma imagem de fundoscopia para análise
                  </p>
                  <p className="text-xs max-w-xs" style={{ color: "var(--text-muted)", opacity: 0.7 }}>
                    O sistema analisa características como microaneurismas, exsudatos, escavação óptica e drusas
                  </p>
                </div>
              )}

              {loading && (
                <div className="h-full flex flex-col items-center justify-center gap-4">
                  <div className="relative">
                    <div className="w-16 h-16 rounded-full border-2 animate-spin" style={{ borderColor: "var(--accent-teal)", borderTopColor: "transparent" }} />
                    <Eye size={18} className="absolute inset-0 m-auto" style={{ color: "var(--accent-teal)" }} />
                  </div>
                  <div className="text-center">
                    <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>Analisando fundoscopia...</p>
                    <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>Extraindo características visuais + RAG</p>
                  </div>
                </div>
              )}

              {error && (
                <div className="flex items-start gap-3 p-4 rounded-xl" style={{ background: "rgba(255,107,107,0.08)", border: "1px solid rgba(255,107,107,0.2)" }}>
                  <AlertTriangle size={16} style={{ color: "var(--accent-red)" }} className="shrink-0 mt-0.5" />
                  <p className="text-sm" style={{ color: "var(--accent-red)" }}>{error}</p>
                </div>
              )}

              {result && (
                <div className="space-y-4 animate-fade-in-up">
                  {/* Main result card */}
                  <div
                    className="p-4 rounded-xl"
                    style={{
                      background: `linear-gradient(135deg, ${severityColor}12, transparent)`,
                      border: `1px solid ${severityColor}40`,
                    }}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-xs font-semibold uppercase tracking-wider mb-1" style={{ color: "var(--text-muted)" }}>
                          Condição Identificada
                        </p>
                        <h3 className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>
                          {result.condition}
                        </h3>
                        <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
                          {result.condition_en}
                        </p>
                      </div>
                      <div className="text-right shrink-0">
                        <div
                          className="text-2xl font-bold"
                          style={{ color: severityColor }}
                        >
                          {Math.round(result.confidence * 100)}%
                        </div>
                        <div
                          className="text-xs px-2 py-0.5 rounded-full mt-1"
                          style={{ background: `${severityColor}20`, color: severityColor, border: `1px solid ${severityColor}40` }}
                        >
                          {result.severity}
                        </div>
                      </div>
                    </div>

                    {/* Confidence bar */}
                    <div className="mt-3 h-1.5 rounded-full" style={{ background: "rgba(255,255,255,0.08)" }}>
                      <div
                        className="h-full rounded-full transition-all"
                        style={{ width: `${result.confidence * 100}%`, background: severityColor }}
                      />
                    </div>
                  </div>

                  {/* Neurological flag */}
                  {result.neurological_flag && (
                    <div
                      className="flex items-start gap-3 p-3 rounded-xl"
                      style={{ background: "rgba(221,160,221,0.08)", border: "1px solid rgba(221,160,221,0.2)" }}
                    >
                      <Brain size={14} style={{ color: "#dda0dd" }} className="shrink-0 mt-0.5" />
                      <div>
                        <p className="text-xs font-semibold mb-0.5" style={{ color: "#dda0dd" }}>
                          Conexão Neurológica
                        </p>
                        <p className="text-xs leading-relaxed" style={{ color: "var(--text-secondary)" }}>
                          {result.neurological_note}
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Features */}
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: "var(--text-muted)" }}>
                      Achados Visuais
                    </p>
                    <ul className="space-y-1">
                      {result.features_detected.map((f, i) => (
                        <li key={i} className="flex items-center gap-2 text-xs" style={{ color: "var(--text-secondary)" }}>
                          <CheckCircle size={11} style={{ color: "var(--accent-teal)", shrink: 0 }} />
                          {f}
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Related structures */}
                  {result.related_structures.length > 0 && (
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: "var(--text-muted)" }}>
                        Estruturas Envolvidas
                      </p>
                      <div className="flex flex-wrap gap-1.5">
                        {result.related_structures.map((s) => (
                          <button
                            key={s}
                            className="structure-badge"
                            onClick={() => { onStructureHighlight(s); onClose(); }}
                          >
                            <Eye size={9} />
                            {s.replace(/_/g, " ")}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* RAG Explanation */}
                  <div>
                    <button
                      className="flex items-center justify-between w-full text-left"
                      onClick={() => setShowExplan((v) => !v)}
                    >
                      <p className="text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--accent-teal)" }}>
                        Explicação Clínica (RAG)
                      </p>
                      {showExplan ? <ChevronUp size={13} style={{ color: "var(--accent-teal)" }} /> : <ChevronDown size={13} style={{ color: "var(--accent-teal)" }} />}
                    </button>
                    {showExplan && (
                      <div
                        className="mt-2 p-3 rounded-xl text-xs leading-relaxed"
                        style={{ background: "rgba(78,205,196,0.05)", border: "1px solid rgba(78,205,196,0.12)", color: "var(--text-secondary)" }}
                      >
                        {result.explanation}
                      </div>
                    )}
                  </div>

                  {/* Classifier method badge */}
                  <div className="flex items-center gap-2">
                    <span
                      className="text-xs px-2 py-0.5 rounded-full"
                      style={result.classifier_method === "claude_vision"
                        ? { background: "rgba(221,160,221,0.12)", border: "1px solid rgba(221,160,221,0.3)", color: "#dda0dd" }
                        : { background: "rgba(78,205,196,0.08)", border: "1px solid rgba(78,205,196,0.2)", color: "var(--text-muted)" }
                      }
                    >
                      {result.classifier_method === "claude_vision" ? "⚡ Claude Vision" : "📊 Análise Visual"}
                    </span>
                  </div>

                  {/* Disclaimer */}
                  <p className="text-xs italic" style={{ color: "var(--text-muted)" }}>
                    ⚠ {result.disclaimer}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
