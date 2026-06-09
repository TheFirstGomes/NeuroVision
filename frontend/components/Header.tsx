"use client";

import { Eye, Activity, Database, ScanEye, BookOpen } from "lucide-react";
import { useEffect, useState } from "react";
import { checkHealth } from "@/lib/api";

interface HeaderProps {
  onOpenCases: () => void;
  onOpenClassifier: () => void;
  onOpenIngest: () => void;
  onResetViewer: () => void;
  onOpenVisualField: () => void;
}

export default function Header({ onOpenCases, onOpenClassifier, onOpenIngest, onResetViewer, onOpenVisualField }: HeaderProps) {
  const [apiStatus, setApiStatus] = useState<"online" | "offline" | "checking">("checking");

  useEffect(() => {
    const check = async () => {
      try {
        const health = await checkHealth();
        setApiStatus(health.rag_ready ? "online" : "checking");
      } catch {
        setApiStatus("offline");
      }
    };
    check();
    const interval = setInterval(check, 15000);
    return () => clearInterval(interval);
  }, []);

  const statusConfig = {
    online:   { color: "#4ade80", label: "Backend online",  pulse: true  },
    offline:  { color: "#ff6b6b", label: "Backend offline", pulse: false },
    checking: { color: "#ffe66d", label: "Conectando...",   pulse: true  },
  };
  const status = statusConfig[apiStatus];

  return (
    <header
      className="flex items-center justify-between px-6 py-3 border-b shrink-0"
      style={{ background: "rgba(5,13,26,0.9)", borderColor: "var(--border)", backdropFilter: "blur(12px)" }}
    >
      {/* Logo */}
      <div className="flex items-center gap-3">
        <div
          className="w-8 h-8 rounded-lg flex items-center justify-center"
          style={{ background: "linear-gradient(135deg, rgba(78,205,196,0.3), rgba(14,165,233,0.2))", border: "1px solid rgba(78,205,196,0.4)" }}
        >
          <Eye size={16} style={{ color: "var(--accent-teal)" }} />
        </div>
        <div>
          <h1 className="text-base font-bold tracking-tight glow-text" style={{ color: "var(--accent-teal)" }}>
            NeuroVision
          </h1>
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>
            Neuro-Oftalmologia Interativa
          </p>
        </div>
      </div>

      {/* Center nav */}
      <div className="hidden md:flex items-center gap-1">
        {[
          { label: "Anatomia 3D",  action: onResetViewer    },
          { label: "Patologias",   action: onOpenCases      },
          { label: "Via Visual",   action: onOpenVisualField },
          { label: "Diagnóstico",  action: onOpenClassifier  },
        ].map(({ label, action }) => (
          <button
            key={label}
            onClick={action}
            className="px-3 py-1.5 rounded-lg text-xs font-medium transition-all hover:bg-white/5"
            style={{ color: "var(--text-secondary)" }}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Right */}
      <div className="flex items-center gap-3">
        {/* Status */}
        <div className="flex items-center gap-1.5">
          <div className="relative">
            <div className="w-2 h-2 rounded-full" style={{ background: status.color }} />
            {status.pulse && (
              <div className="absolute inset-0 w-2 h-2 rounded-full animate-ping" style={{ background: status.color, opacity: 0.4 }} />
            )}
          </div>
          <span className="text-xs" style={{ color: "var(--text-muted)" }}>{status.label}</span>
        </div>

        {/* Cases button */}
        <button
          onClick={onOpenCases}
          className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-all glass-hover"
          style={{
            background: "rgba(152,221,202,0.08)",
            border: "1px solid rgba(152,221,202,0.2)",
            color: "#98ddca",
          }}
          title="Casos clínicos educacionais"
        >
          <BookOpen size={12} />
          <span className="hidden md:inline">Casos</span>
        </button>

        {/* Classifier button */}
        <button
          onClick={onOpenClassifier}
          className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-all glass-hover"
          style={{
            background: "rgba(221,160,221,0.08)",
            border: "1px solid rgba(221,160,221,0.2)",
            color: "#dda0dd",
          }}
          title="Analisar imagem de fundoscopia"
        >
          <ScanEye size={12} />
          <span className="hidden md:inline">Fundoscopia</span>
        </button>

        {/* Knowledge Base button */}
        <button
          onClick={onOpenIngest}
          className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-all glass-hover"
          style={{
            background: "rgba(78,205,196,0.08)",
            border: "1px solid rgba(78,205,196,0.2)",
            color: "var(--accent-teal)",
          }}
          title="Gerenciar base de conhecimento RAG"
        >
          <Database size={12} />
          <span className="hidden md:inline">Base RAG</span>
        </button>

        {/* Phase badge */}
        <div
          className="flex items-center gap-1.5 px-2 py-1 rounded-lg text-xs"
          style={{ background: "rgba(78,205,196,0.08)", border: "1px solid rgba(78,205,196,0.15)", color: "var(--text-muted)" }}
        >
          <Activity size={11} style={{ color: "var(--accent-teal)" }} />
          <span>Fase 2</span>
        </div>
      </div>
    </header>
  );
}
