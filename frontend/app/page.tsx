"use client";

/**
 * NeuroVision — Main page
 * Layout: Header | 3D Viewer (full) | Tabbed sidebar (Chat · Anatomia · Campo Visual)
 *
 * The 3D viewer is always unobstructed.
 * Selecting a structure auto-switches the sidebar to the Anatomy tab.
 * "Perguntar ao Tutor" auto-switches to Chat.
 */

import { useState, useCallback, useEffect } from "react";
import dynamic from "next/dynamic";
import { MessageSquare, Eye, Activity, Box, Image as ImageIcon } from "lucide-react";
import EyeViewer2D from "@/components/EyeViewer2D";
import Header from "@/components/Header";
import AnatomyPanel from "@/components/AnatomyPanel";
import ChatPanel from "@/components/ChatPanel";
import VisualFieldPanel from "@/components/VisualFieldPanel";
import CasesPanel from "@/components/CasesPanel";
import ImageClassifier from "@/components/ImageClassifier";
import IngestPanel from "@/components/IngestPanel";

const EyeViewer3D = dynamic(() => import("@/components/EyeViewer3D"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full flex items-center justify-center">
      <div className="text-center space-y-3">
        <div className="flex justify-center gap-2">
          {[0, 1, 2].map((i) => (
            <div key={i} className="loading-dot w-3 h-3 rounded-full" style={{ background: "var(--accent-teal)" }} />
          ))}
        </div>
        <p className="text-sm" style={{ color: "var(--text-muted)" }}>Carregando modelo 3D...</p>
      </div>
    </div>
  ),
});

type SidebarTab = "chat" | "anatomy" | "field";

const TABS: { id: SidebarTab; label: string; icon: React.ReactNode; requiresStructure?: boolean }[] = [
  { id: "chat",    label: "Chat",         icon: <MessageSquare size={12} /> },
  { id: "anatomy", label: "Anatomia",     icon: <Eye size={12} />,      requiresStructure: true },
  { id: "field",   label: "Campo Visual", icon: <Activity size={12} />, requiresStructure: true },
];

export default function Page() {
  const [selectedStructure, setSelectedStructure] = useState<string | null>(null);
  const [injectedMessage, setInjectedMessage]     = useState<string | undefined>();
  const [activeTab, setActiveTab]                 = useState<SidebarTab>("chat");

  // Viewer mode
  const [viewMode, setViewMode] = useState<"3d" | "2d">("3d");

  // Fiber region selected via 3D nerve bundle click → drives VisualFieldPanel
  const [selectedFiberRegion, setSelectedFiberRegion] = useState<string | null>(null);

  // Modal visibility
  const [showCases,      setShowCases]      = useState(false);
  const [showClassifier, setShowClassifier] = useState(false);
  const [showIngest,     setShowIngest]     = useState(false);

  // Auto-switch to Anatomy when a structure is selected
  useEffect(() => {
    if (selectedStructure) setActiveTab("anatomy");
  }, [selectedStructure]);

  const handleStructureSelect = useCallback((id: string | null) => {
    setSelectedStructure(id);
    if (!id) {
      setActiveTab("chat");
      setSelectedFiberRegion(null);
    }
    // Clear fiber region when switching away from the optic nerve context
    if (id && id !== "nervo_optico") setSelectedFiberRegion(null);
  }, []);

  // Fiber strand clicked in 3D viewer → switch to Campo Visual tab with fiber annotation
  const handleFiberRegionClick = useCallback((regionId: string) => {
    // Auto-select the optic nerve if nothing is selected, so the field tab is enabled
    if (!selectedStructure) setSelectedStructure("nervo_optico");
    setSelectedFiberRegion(regionId);
    setActiveTab("field");
  }, [selectedStructure]);

  // Inject question into chat AND switch to Chat tab
  const handleAskAbout = useCallback((question: string) => {
    setInjectedMessage(question);
    setActiveTab("chat");
  }, []);

  const handleInitialMessageConsumed = useCallback(() => {
    setInjectedMessage(undefined);
  }, []);

  return (
    <div className="flex flex-col" style={{ height: "100vh", background: "var(--bg-primary)" }}>
      <Header
        onOpenCases={() => setShowCases(true)}
        onOpenClassifier={() => setShowClassifier(true)}
        onOpenIngest={() => setShowIngest(true)}
        onResetViewer={() => handleStructureSelect(null)}
        onOpenVisualField={() => {
          if (selectedStructure) setActiveTab("field");
          else setActiveTab("chat"); // sem estrutura selecionada, redireciona ao chat
        }}
      />

      <main className="flex flex-1 overflow-hidden">

        {/* ── Viewer (3D or 2D) ── */}
        <div
          className="relative flex-1"
          style={{ borderRight: "1px solid var(--border)" }}
        >
          {/* 2D / 3D toggle */}
          <div className="absolute top-3 left-3 z-20 flex rounded-lg overflow-hidden"
            style={{ border: "1px solid var(--border)", background: "rgba(5,13,26,0.85)" }}
          >
            {(["3d", "2d"] as const).map((mode) => {
              const active = viewMode === mode;
              return (
                <button
                  key={mode}
                  onClick={() => setViewMode(mode)}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium transition-all"
                  style={{
                    color: active ? "var(--accent-teal)" : "var(--text-muted)",
                    background: active ? "rgba(78,205,196,0.1)" : "transparent",
                    borderRight: mode === "3d" ? "1px solid var(--border)" : "none",
                  }}
                >
                  {mode === "3d"
                    ? <><Box size={11} /><span>3D</span></>
                    : <><ImageIcon size={11} /><span>2D</span></>
                  }
                </button>
              );
            })}
          </div>

          {viewMode === "3d" ? (
            <>
              {/* Background grid */}
              <div
                className="absolute inset-0 pointer-events-none"
                style={{
                  background: "radial-gradient(ellipse at center, rgba(14,165,233,0.06) 0%, var(--bg-primary) 70%)",
                  backgroundImage:
                    "linear-gradient(rgba(78,205,196,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(78,205,196,0.03) 1px, transparent 1px)",
                  backgroundSize: "40px 40px",
                }}
              />
              <EyeViewer3D
                selectedStructure={selectedStructure}
                onStructureSelect={handleStructureSelect}
                onFiberRegionClick={handleFiberRegionClick}
              />
              {/* Legend */}
              <div className="absolute bottom-4 right-4 z-10 space-y-1">
                {[
                  { color: "#ff6b6b", label: "Origem (retina)" },
                  { color: "#f0c040", label: "Condução (nervo)" },
                  { color: "#ff9f43", label: "Decussação (quiasma)" },
                  { color: "#4ade80", label: "Projeção (trato → CGL)" },
                  { color: "#74d7f7", label: "Processamento (córtex)" },
                ].map((item) => (
                  <div key={item.label} className="flex items-center gap-1.5">
                    <div className="w-2 h-2 rounded-full" style={{ background: item.color }} />
                    <span className="text-xs" style={{ color: "var(--text-muted)" }}>{item.label}</span>
                  </div>
                ))}
              </div>
              {!selectedStructure && (
                <div className="absolute bottom-4 left-1/2 -translate-x-1/2 pointer-events-none">
                  <p className="text-xs px-3 py-1.5 rounded-full"
                    style={{ background: "rgba(5,13,26,0.7)", border: "1px solid var(--border)", color: "var(--text-muted)" }}>
                    Clique em uma estrutura para explorar
                  </p>
                </div>
              )}
            </>
          ) : (
            <EyeViewer2D
              selectedStructure={selectedStructure}
              onStructureSelect={handleStructureSelect}
            />
          )}
        </div>

        {/* ── Tabbed sidebar ── */}
        <div
          className="flex flex-col shrink-0"
          style={{ width: "clamp(300px, 32vw, 440px)", background: "var(--bg-secondary)" }}
        >
          {/* Tab bar */}
          <div
            className="flex shrink-0 border-b"
            style={{ borderColor: "var(--border)", background: "rgba(5,13,26,0.6)" }}
          >
            {TABS.map((tab) => {
              const disabled = !!tab.requiresStructure && !selectedStructure;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  disabled={disabled}
                  onClick={() => setActiveTab(tab.id)}
                  className="flex-1 flex items-center justify-center gap-1.5 py-2.5 text-xs font-medium transition-all"
                  style={{
                    color: isActive ? "var(--accent-teal)" : "var(--text-muted)",
                    borderBottom: isActive ? "2px solid var(--accent-teal)" : "2px solid transparent",
                    opacity: disabled ? 0.35 : 1,
                    cursor: disabled ? "not-allowed" : "pointer",
                  }}
                >
                  {tab.icon}
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>

          {/* Tab content */}
          <div className="flex-1 overflow-hidden flex flex-col">

            {/* Chat — kept mounted to preserve conversation history */}
            <div style={{ display: activeTab === "chat" ? "flex" : "none", flexDirection: "column", flex: 1, overflow: "hidden" }}>
              <ChatPanel
                selectedStructure={selectedStructure}
                onStructureHighlight={handleStructureSelect}
                initialMessage={injectedMessage}
                onInitialMessageConsumed={handleInitialMessageConsumed}
              />
            </div>

            {/* Anatomy — mounted only when visible (re-fetches on tab open) */}
            {activeTab === "anatomy" && (
              <div style={{ flex: 1, overflow: "hidden" }}>
                <AnatomyPanel
                  structureId={selectedStructure}
                  onClose={() => handleStructureSelect(null)}
                  onAskAbout={handleAskAbout}
                />
              </div>
            )}

            {/* Visual Field */}
            {activeTab === "field" && (
              <div style={{ flex: 1, overflow: "hidden" }}>
                <VisualFieldPanel
                  structureId={selectedStructure}
                  fiberRegion={selectedFiberRegion}
                />
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Modals — rendered here so they have access to page-level state */}
      {showCases && (
        <CasesPanel
          onClose={() => setShowCases(false)}
          onStructureHighlight={(id) => {
            handleStructureSelect(id);
            setShowCases(false);
          }}
        />
      )}
      {showClassifier && (
        <ImageClassifier
          onClose={() => setShowClassifier(false)}
          onStructureHighlight={(id) => {
            handleStructureSelect(id);
            setShowClassifier(false);
          }}
        />
      )}
      {showIngest && <IngestPanel onClose={() => setShowIngest(false)} />}

      {/* Footer */}
      <footer
        className="px-6 py-2 border-t flex items-center justify-between shrink-0"
        style={{ borderColor: "var(--border)", background: "rgba(5,13,26,0.9)" }}
      >
        <p className="text-xs" style={{ color: "var(--text-muted)" }}>
          Ferramenta educacional · Não substitui diagnóstico clínico
        </p>
        <p className="text-xs" style={{ color: "var(--text-muted)" }}>
          Fontes: IMO, Walsh & Hoyt, Lancet Neurology, PubMed · Fase 2
        </p>
      </footer>
    </div>
  );
}
