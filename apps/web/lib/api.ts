import { BrainState, ChatResponse, Concept, GraphData } from "@/types";

// Production: NEXT_PUBLIC_API_URL points at the Render-hosted FastAPI backend.
// Development: falls back to relative /api (rewritten by next.config.js rewrites).
const API_BASE = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "/api";

const isFullUrl = (base: string): boolean => /^https?:\/\//.test(base);

const pathFor = (path: string): string =>
  isFullUrl(API_BASE) ? `${API_BASE}${path}` : path;

export async function sendMessage(message: string): Promise<ChatResponse> {
  const response = await fetch(pathFor("/api/chat"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ message }),
  });

  if (!response.ok) {
    throw new Error(`Chat request failed: ${response.statusText}`);
  }

  return response.json();
}

export async function getBrainState(): Promise<BrainState> {
  const response = await fetch(pathFor("/api/brain/state"));

  if (!response.ok) {
    throw new Error(`Brain state request failed: ${response.statusText}`);
  }

  return response.json();
}

export async function getConcepts(): Promise<Concept[]> {
  const response = await fetch(pathFor("/api/brain/concepts"));

  if (!response.ok) {
    throw new Error(`Concepts request failed: ${response.statusText}`);
  }

  return response.json();
}

export async function getGraph(): Promise<GraphData> {
  const response = await fetch(pathFor("/api/brain/graph"));

  if (!response.ok) {
    throw new Error(`Graph request failed: ${response.statusText}`);
  }

  return response.json();
}
