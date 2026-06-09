/**
 * API client for NeuroVision backend.
 * All communication with FastAPI goes through here.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  sources?: string[];
  relatedStructures?: string[];
  timestamp: Date;
}

export interface ChatRequest {
  message: string;
  session_id?: string;
  structure?: string;
}

export interface ChatResponse {
  answer: string;
  sources: string[];
  related_structures: string[];
  session_id: string;
}

export interface AnatomyStructure {
  id: string;
  name: string;
  description: string;
  neurological_connections: string[];
  associated_pathologies: string[];
  clinical_relevance: string;
}

export interface AnatomyResponse {
  structure: AnatomyStructure;
  highlight_color: string;
}

export async function sendChatMessage(payload: ChatRequest): Promise<ChatResponse> {
  const response = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Erro desconhecido" }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

export async function fetchAnatomyStructure(structureId: string): Promise<AnatomyResponse> {
  const response = await fetch(`${API_URL}/anatomy/${structureId}`);

  if (!response.ok) {
    throw new Error(`Structure not found: ${structureId}`);
  }

  return response.json();
}

export async function checkHealth(): Promise<{ status: string; rag_ready: boolean }> {
  const response = await fetch(`${API_URL}/health`);
  return response.json();
}

// ── Clinical Cases ────────────────────────────────────────────────────────────

export interface CaseListItem {
  id: string;
  title: string;
  category: string;
  difficulty: number;
  related_structure: string;
}

export interface CaseQuestion {
  question: string;
  answer: string;
  explanation: string;
}

export interface CasePatient {
  age: number;
  sex: string;
  chief_complaint: string;
  history: string;
  examination: string;
}

export interface ClinicalCase {
  id: string;
  title: string;
  category: string;
  difficulty: number;
  related_structure: string;
  visual_field_structure: string;
  patient: CasePatient;
  questions: CaseQuestion[];
  teaching_point: string;
}

export async function fetchCases(): Promise<CaseListItem[]> {
  const response = await fetch(`${API_URL}/cases`);
  if (!response.ok) throw new Error("Falha ao carregar casos clínicos");
  return response.json();
}

export async function fetchCase(caseId: string): Promise<ClinicalCase> {
  const response = await fetch(`${API_URL}/cases/${caseId}`);
  if (!response.ok) throw new Error(`Caso ${caseId} não encontrado`);
  return response.json();
}

// ── Session history ───────────────────────────────────────────────────────────

export interface SessionMessage {
  role: "user" | "assistant";
  content: string;
  sources: string[];
  related_structures: string[];
  created_at: string;
}

export interface SessionHistoryResponse {
  session_id: string;
  messages: SessionMessage[];
}

export async function fetchSessionMessages(sessionId: string): Promise<SessionHistoryResponse> {
  const response = await fetch(`${API_URL}/sessions/${sessionId}/messages`);
  if (!response.ok) throw new Error(`Session ${sessionId} not found`);
  return response.json();
}
