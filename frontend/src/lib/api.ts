import type {
  ChatRequest,
  GraphData,
  IngestRequest,
  IngestResponse,
  SearchResponse,
} from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function searchPapers(query: string, limit = 20): Promise<SearchResponse> {
  const res = await fetch(`${BASE}/api/search?q=${encodeURIComponent(query)}&limit=${limit}`);
  if (!res.ok) throw new Error(`Search failed: ${res.statusText}`);
  return res.json();
}

export async function ingestSource(request: IngestRequest): Promise<IngestResponse> {
  const res = await fetch(`${BASE}/api/ingest`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!res.ok) throw new Error(`Ingest failed: ${res.statusText}`);
  return res.json();
}

export async function ingestPDF(file: File): Promise<IngestResponse> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${BASE}/api/ingest/pdf`, { method: "POST", body: form });
  if (!res.ok) throw new Error(`PDF ingest failed: ${res.statusText}`);
  return res.json();
}

export async function getGraph(limit = 200): Promise<GraphData> {
  const res = await fetch(`${BASE}/api/graph?limit=${limit}`);
  if (!res.ok) throw new Error(`Graph fetch failed: ${res.statusText}`);
  const data = await res.json();
  // react-force-graph expects "links" not "edges"
  return { nodes: data.nodes, links: data.edges };
}

/**
 * Streams a chat response from the server.
 * Calls onToken for each text token, onDone when complete.
 */
export async function streamChat(
  request: ChatRequest,
  onToken: (token: string) => void,
  onDone: (intent: string) => void,
  onError: (err: Error) => void,
): Promise<void> {
  try {
    const res = await fetch(`${BASE}/api/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });
    if (!res.ok) throw new Error(`Chat failed: ${res.statusText}`);

    const reader = res.body?.getReader();
    if (!reader) return;

    const decoder = new TextDecoder();
    let intent = "qa";
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        const payload = line.slice(6).trim();
        if (payload === "[DONE]") {
          onDone(intent);
          return;
        }
        try {
          const parsed = JSON.parse(payload);
          if (parsed.type === "intent") intent = parsed.intent;
          if (parsed.type === "text") onToken(parsed.content);
        } catch {
          // ignore malformed lines
        }
      }
    }
    onDone(intent);
  } catch (err) {
    onError(err instanceof Error ? err : new Error(String(err)));
  }
}
