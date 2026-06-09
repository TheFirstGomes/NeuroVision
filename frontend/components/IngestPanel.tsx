"use client";

/**
 * PDF Ingestion Panel
 * Allows uploading neuro-ophthalmology literature PDFs to expand the RAG knowledge base.
 */

import { useState, useCallback, useEffect, useRef } from "react";
import { X, Upload, FileText, CheckCircle, AlertCircle, Loader2, Database, BookOpen } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Source {
  source: string;
  topic: string;
  chunks: number;
}

interface IngestResult {
  filename: string;
  pages: number;
  chunks_added: number;
  skipped: boolean;
  reason?: string;
}

interface IngestPanelProps {
  onClose: () => void;
}

export default function IngestPanel({ onClose }: IngestPanelProps) {
  const [sources, setSources] = useState<Source[]>([]);
  const [totalChunks, setTotalChunks] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [results, setResults] = useState<IngestResult[]>([]);
  const [dragOver, setDragOver] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const loadDocuments = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/documents`);
      if (!res.ok) return;
      const data = await res.json();
      setSources(data.sources || []);
      setTotalChunks(data.total_chunks || 0);
    } catch {
      // backend offline — silently ignore
    }
  }, []);

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  const uploadFiles = useCallback(async (files: FileList | File[]) => {
    const pdfs = Array.from(files).filter((f) => f.name.toLowerCase().endsWith(".pdf"));
    if (!pdfs.length) return;

    setUploading(true);
    const newResults: IngestResult[] = [];

    for (const file of pdfs) {
      const form = new FormData();
      form.append("file", file);

      try {
        const res = await fetch(`${API_URL}/ingest`, { method: "POST", body: form });
        const data = await res.json();

        if (!res.ok) {
          newResults.push({
            filename: file.name,
            pages: 0,
            chunks_added: 0,
            skipped: false,
            reason: data.detail || "Erro desconhecido",
          });
        } else {
          newResults.push(data);
        }
      } catch {
        newResults.push({
          filename: file.name,
          pages: 0,
          chunks_added: 0,
          skipped: false,
          reason: "Falha na conexão com o backend",
        });
      }
    }

    setResults((prev) => [...newResults, ...prev]);
    setUploading(false);
    loadDocuments();
  }, [loadDocuments]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    uploadFiles(e.dataTransfer.files);
  }, [uploadFiles]);

  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) uploadFiles(e.target.files);
  }, [uploadFiles]);

  const isBuiltIn = (source: string) =>
    !source.toLowerCase().endsWith(".pdf");

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ background: "rgba(0,0,0,0.6)", backdropFilter: "blur(4px)" }}>
      <div
        className="glass rounded-2xl w-full max-w-lg flex flex-col"
        style={{ maxHeight: "85vh", border: "1px solid rgba(78,205,196,0.25)" }}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b" style={{ borderColor: "var(--border)" }}>
          <div className="flex items-center gap-2">
            <Database size={16} style={{ color: "var(--accent-teal)" }} />
            <h2 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
              Base de Conhecimento RAG
            </h2>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs px-2 py-0.5 rounded-full" style={{ background: "rgba(78,205,196,0.12)", border: "1px solid rgba(78,205,196,0.25)", color: "var(--accent-teal)" }}>
              {totalChunks} chunks indexados
            </span>
            <button onClick={onClose} className="p-1 rounded-lg hover:bg-white/5 transition-colors" style={{ color: "var(--text-muted)" }}>
              <X size={15} />
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-5 space-y-5">
          {/* Upload zone */}
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider mb-3" style={{ color: "var(--text-muted)" }}>
              Adicionar Literatura
            </p>
            <div
              className="rounded-xl border-2 border-dashed p-6 text-center cursor-pointer transition-all"
              style={{
                borderColor: dragOver ? "var(--accent-teal)" : "var(--border)",
                background: dragOver ? "rgba(78,205,196,0.06)" : "rgba(13,31,53,0.4)",
              }}
              onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleDrop}
              onClick={() => fileRef.current?.click()}
            >
              <input
                ref={fileRef}
                type="file"
                accept=".pdf"
                multiple
                className="hidden"
                onChange={handleFileChange}
              />
              {uploading ? (
                <div className="flex flex-col items-center gap-2">
                  <Loader2 size={24} className="animate-spin" style={{ color: "var(--accent-teal)" }} />
                  <p className="text-sm" style={{ color: "var(--text-secondary)" }}>Processando PDF...</p>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-2">
                  <Upload size={24} style={{ color: dragOver ? "var(--accent-teal)" : "var(--text-muted)" }} />
                  <p className="text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
                    Arraste PDFs aqui ou clique para selecionar
                  </p>
                  <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                    Artigos PubMed, IMO, Lancet, Walsh & Hoyt · Máx 50MB
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Upload results */}
          {results.length > 0 && (
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: "var(--text-muted)" }}>
                Últimas Ingestões
              </p>
              <div className="space-y-2">
                {results.map((r, i) => (
                  <div
                    key={i}
                    className="flex items-start gap-3 p-3 rounded-lg"
                    style={{
                      background: r.reason
                        ? "rgba(255,107,107,0.08)"
                        : r.skipped
                        ? "rgba(255,230,109,0.08)"
                        : "rgba(78,205,196,0.08)",
                      border: `1px solid ${r.reason ? "rgba(255,107,107,0.2)" : r.skipped ? "rgba(255,230,109,0.2)" : "rgba(78,205,196,0.2)"}`,
                    }}
                  >
                    {r.reason ? (
                      <AlertCircle size={14} className="mt-0.5 shrink-0" style={{ color: "var(--accent-red)" }} />
                    ) : r.skipped ? (
                      <CheckCircle size={14} className="mt-0.5 shrink-0" style={{ color: "var(--accent-yellow)" }} />
                    ) : (
                      <CheckCircle size={14} className="mt-0.5 shrink-0" style={{ color: "var(--accent-teal)" }} />
                    )}
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium truncate" style={{ color: "var(--text-primary)" }}>
                        {r.filename}
                      </p>
                      <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
                        {r.reason
                          ? r.reason
                          : r.skipped
                          ? "Já indexado — sem duplicatas"
                          : `${r.pages} páginas · ${r.chunks_added} chunks adicionados`}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Indexed sources */}
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: "var(--text-muted)" }}>
              Fontes Indexadas
            </p>
            <div className="space-y-1.5">
              {sources.length === 0 ? (
                <p className="text-xs text-center py-3" style={{ color: "var(--text-muted)" }}>
                  Carregando...
                </p>
              ) : (
                sources.map((s) => (
                  <div
                    key={s.source}
                    className="flex items-center justify-between px-3 py-2 rounded-lg"
                    style={{ background: "rgba(13,31,53,0.6)", border: "1px solid var(--border)" }}
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      {isBuiltIn(s.source) ? (
                        <BookOpen size={12} style={{ color: "var(--accent-teal)", shrink: 0 }} />
                      ) : (
                        <FileText size={12} style={{ color: "var(--accent-blue)", shrink: 0 }} />
                      )}
                      <span className="text-xs truncate" style={{ color: "var(--text-secondary)" }}>
                        {s.source}
                      </span>
                    </div>
                    <span
                      className="text-xs shrink-0 ml-2 px-2 py-0.5 rounded-full"
                      style={{ background: "rgba(78,205,196,0.1)", color: "var(--accent-teal)" }}
                    >
                      {s.chunks}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t text-xs" style={{ borderColor: "var(--border)", color: "var(--text-muted)" }}>
          Chunks são indexados no ChromaDB e ficam disponíveis imediatamente para o chat RAG.
        </div>
      </div>
    </div>
  );
}
