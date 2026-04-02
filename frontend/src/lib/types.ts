export type IngestionSource = "arxiv" | "semantic_scholar" | "pdf" | "url" | "web_search";

export interface IngestRequest {
  source: IngestionSource;
  query?: string;
  url?: string;
  max_results?: number;
}

export interface IngestResponse {
  ingested: number;
  papers: Paper[];
  web_content: WebContent[];
}

export interface Paper {
  id: string;
  title: string;
  abstract?: string;
  published_date?: string;
  url?: string;
  doi?: string;
  source?: string;
  authors?: string[];
  categories?: string[];
}

export interface WebContent {
  id: string;
  title: string;
  url?: string;
  content?: string;
  source_type?: string;
  published_date?: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  intent?: string;
  sources?: SearchResult[];
}

export interface ChatRequest {
  message: string;
  history: { role: string; content: string }[];
  context_paper_ids?: string[];
}

export interface SearchResult {
  id: string;
  type: string;
  title: string;
  snippet: string;
  url?: string;
  score?: number;
  metadata?: Record<string, unknown>;
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
}

export interface GraphNode {
  id: string;
  label: string;
  type: "Paper" | "Author" | "Concept" | "Institution" | "WebContent";
  properties: Record<string, unknown>;
  // react-force-graph dynamic fields
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
  fx?: number;
  fy?: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  relationship: string;
  properties: Record<string, unknown>;
}

export interface GraphData {
  nodes: GraphNode[];
  links: GraphEdge[];
}
