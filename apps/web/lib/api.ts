import { BrainState, ChatResponse, Concept, GraphData } from "@/types";

const API_BASE = "/api";

export async function sendMessage(message: string): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE}/chat`, {
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
  const response = await fetch(`${API_BASE}/brain/state`);

  if (!response.ok) {
    throw new Error(`Brain state request failed: ${response.statusText}`);
  }

  return response.json();
}

export async function getConcepts(): Promise<Concept[]> {
  const response = await fetch(`${API_BASE}/brain/concepts`);

  if (!response.ok) {
    throw new Error(`Concepts request failed: ${response.statusText}`);
  }

  return response.json();
}

export async function getGraph(): Promise<GraphData> {
  const response = await fetch(`${API_BASE}/brain/graph`);

  if (!response.ok) {
    throw new Error(`Graph request failed: ${response.statusText}`);
  }

  return response.json();
}
