"use client";

/**
 * Educational chat panel with RAG-powered responses.
 * Connects to the FastAPI backend /chat endpoint.
 */

import { useState, useRef, useEffect, useCallback } from "react";
import { Send, Bot, User, BookOpen, ExternalLink, Loader2 } from "lucide-react";
import { sendChatMessage, fetchSessionMessages, ChatMessage } from "@/lib/api";
import { STRUCTURE_MAP } from "@/lib/anatomy-data";

const WELCOME_MESSAGE = {
  role: "assistant" as const,
  content:
    "Olá! Sou o **NeuroVision**, seu tutor de neuro-oftalmologia.\n\nClique em qualquer estrutura no modelo 3D para explorar sua anatomia e relações neurológicas — ou faça uma pergunta diretamente.\n\nTodas as respostas são baseadas em literatura médica peer-reviewed.",
  timestamp: new Date(),
};

const SUGGESTED_QUESTIONS = [
  "O que é neurite óptica e qual sua relação com a esclerose múltipla?",
  "Qual o significado clínico do papiledema?",
  "Como o adenoma hipofisário afeta a visão?",
  "Explique a hemianopsia bitemporal",
  "O que é síndrome de Horner?",
  "Qual a diferença entre NOIA arterítica e não-arterítica?",
];

interface ChatPanelProps {
  selectedStructure: string | null;
  onStructureHighlight: (id: string) => void;
  initialMessage?: string;
  onInitialMessageConsumed?: () => void;
}

export default function ChatPanel({
  selectedStructure,
  onStructureHighlight,
  initialMessage,
  onInitialMessageConsumed,
}: ChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([WELCOME_MESSAGE]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | undefined>();
  const [historyLoaded, setHistoryLoaded] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Restore session from localStorage on first mount
  useEffect(() => {
    if (historyLoaded) return;
    setHistoryLoaded(true);

    const storedId = typeof window !== "undefined"
      ? localStorage.getItem("neurovision_session_id")
      : null;

    if (!storedId) return;

    setSessionId(storedId);

    fetchSessionMessages(storedId)
      .then((history) => {
        if (history.messages.length === 0) return;
        const restored: ChatMessage[] = history.messages.map((m) => ({
          role: m.role,
          content: m.content,
          sources: m.sources.length > 0 ? m.sources : undefined,
          relatedStructures: m.related_structures.length > 0 ? m.related_structures : undefined,
          timestamp: new Date(m.created_at),
        }));
        setMessages([WELCOME_MESSAGE, ...restored]);
      })
      .catch(() => {
        // Session may have been deleted or DB is fresh — silently ignore
        localStorage.removeItem("neurovision_session_id");
      });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Handle external message injection (from anatomy panel)
  useEffect(() => {
    if (initialMessage) {
      setInput(initialMessage);
      inputRef.current?.focus();
      onInitialMessageConsumed?.();
    }
  }, [initialMessage, onInitialMessageConsumed]);

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || loading) return;

      const userMessage: ChatMessage = {
        role: "user",
        content: text.trim(),
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, userMessage]);
      setInput("");
      setLoading(true);

      try {
        const response = await sendChatMessage({
          message: text.trim(),
          session_id: sessionId,
          structure: selectedStructure || undefined,
        });

        if (!sessionId && typeof window !== "undefined") {
          localStorage.setItem("neurovision_session_id", response.session_id);
        }
        setSessionId(response.session_id);

        const assistantMessage: ChatMessage = {
          role: "assistant",
          content: response.answer,
          sources: response.sources,
          relatedStructures: response.related_structures,
          timestamp: new Date(),
        };

        setMessages((prev) => [...prev, assistantMessage]);
      } catch (err) {
        const errorMessage: ChatMessage = {
          role: "assistant",
          content:
            "⚠️ Não foi possível conectar ao servidor. Verifique se o backend está rodando em `http://localhost:8000`.",
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, errorMessage]);
      } finally {
        setLoading(false);
      }
    },
    [loading, sessionId, selectedStructure]
  );

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  };

  const formatContent = (content: string) => {
    return content
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
      .replace(/\n/g, "<br/>");
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-4 py-3 border-b" style={{ borderColor: "var(--border)" }}>
        <div className="flex items-center gap-2">
          <div
            className="w-7 h-7 rounded-lg flex items-center justify-center"
            style={{ background: "rgba(78,205,196,0.15)", border: "1px solid rgba(78,205,196,0.3)" }}
          >
            <Bot size={14} style={{ color: "var(--accent-teal)" }} />
          </div>
          <div>
            <h2 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
              Tutor NeuroVision
            </h2>
            <p className="text-xs" style={{ color: "var(--text-muted)" }}>
              Baseado em literatura peer-reviewed
            </p>
          </div>
          {selectedStructure && (
            <div className="ml-auto structure-badge">
              {STRUCTURE_MAP.get(selectedStructure)?.label ?? selectedStructure}
            </div>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
        {/* Suggested questions — shown only at start */}
        {messages.length === 1 && (
          <div className="space-y-1.5">
            <p className="text-xs font-medium mb-2" style={{ color: "var(--text-muted)" }}>
              Perguntas sugeridas:
            </p>
            {SUGGESTED_QUESTIONS.map((q, i) => (
              <button
                key={i}
                onClick={() => sendMessage(q)}
                className="w-full text-left text-xs px-3 py-2 rounded-lg transition-all glass-hover"
                style={{
                  background: "rgba(78,205,196,0.05)",
                  border: "1px solid rgba(78,205,196,0.1)",
                  color: "var(--text-secondary)",
                }}
              >
                {q}
              </button>
            ))}
          </div>
        )}

        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`animate-fade-in-up ${msg.role === "user" ? "flex justify-end" : "flex justify-start"}`}
          >
            <div className={`max-w-[88%] ${msg.role === "user" ? "message-user" : "message-assistant"} p-3`}>
              <div className="flex items-start gap-2">
                {msg.role === "assistant" && (
                  <Bot size={13} className="mt-0.5 shrink-0" style={{ color: "var(--accent-teal)" }} />
                )}
                {msg.role === "user" && (
                  <User size={13} className="mt-0.5 shrink-0 order-last" style={{ color: "var(--accent-blue)" }} />
                )}
                <div className="flex-1 min-w-0">
                  <p
                    className="text-sm leading-relaxed"
                    style={{ color: "var(--text-primary)" }}
                    dangerouslySetInnerHTML={{ __html: formatContent(msg.content) }}
                  />

                  {/* Sources */}
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-2 pt-2 border-t" style={{ borderColor: "var(--border)" }}>
                      <div className="flex items-center gap-1 mb-1">
                        <BookOpen size={10} style={{ color: "var(--text-muted)" }} />
                        <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                          Fontes
                        </span>
                      </div>
                      <div className="space-y-0.5">
                        {msg.sources.map((src, si) => (
                          <p key={si} className="text-xs" style={{ color: "var(--text-muted)" }}>
                            · {src}
                          </p>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Related structures */}
                  {msg.relatedStructures && msg.relatedStructures.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {msg.relatedStructures.map((s) => (
                        <button
                          key={s}
                          className="structure-badge"
                          onClick={() => onStructureHighlight(s)}
                          title="Destacar no modelo 3D"
                        >
                          <ExternalLink size={9} />
                          {STRUCTURE_MAP.get(s)?.label ?? s}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}

        {/* Loading indicator */}
        {loading && (
          <div className="flex justify-start animate-fade-in-up">
            <div className="message-assistant p-3">
              <div className="flex items-center gap-2">
                <Bot size={13} style={{ color: "var(--accent-teal)" }} />
                <div className="flex gap-1">
                  {[0, 1, 2].map((i) => (
                    <div
                      key={i}
                      className="loading-dot w-2 h-2 rounded-full"
                      style={{ background: "var(--accent-teal)" }}
                    />
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="px-4 py-3 border-t" style={{ borderColor: "var(--border)" }}>
        <div
          className="flex items-end gap-2 rounded-xl p-2 transition-all"
          style={{
            background: "rgba(13,31,53,0.8)",
            border: "1px solid var(--border)",
          }}
        >
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Faça uma pergunta sobre neuro-oftalmologia..."
            rows={1}
            className="flex-1 bg-transparent text-sm resize-none outline-none py-1 px-1"
            style={{
              color: "var(--text-primary)",
              minHeight: "36px",
              maxHeight: "120px",
            }}
          />
          <button
            onClick={() => sendMessage(input)}
            disabled={!input.trim() || loading}
            className="p-2 rounded-lg transition-all shrink-0"
            style={{
              background: input.trim() && !loading ? "rgba(78,205,196,0.2)" : "transparent",
              color: input.trim() && !loading ? "var(--accent-teal)" : "var(--text-muted)",
              border: "1px solid",
              borderColor:
                input.trim() && !loading ? "rgba(78,205,196,0.4)" : "transparent",
            }}
          >
            {loading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
          </button>
        </div>
        <p className="text-center text-xs mt-1.5" style={{ color: "var(--text-muted)" }}>
          Enter para enviar · Shift+Enter para quebrar linha
        </p>
      </div>
    </div>
  );
}
