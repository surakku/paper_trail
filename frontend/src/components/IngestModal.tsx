"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ingestSource, ingestPDF } from "@/lib/api";
import type { IngestionSource } from "@/lib/types";
import { X, Upload, Search, Globe, FileText } from "lucide-react";

interface IngestModalProps {
  onClose: () => void;
  onSuccess: (count: number) => void;
}

const SOURCES: { id: IngestionSource; label: string; icon: React.ReactNode; placeholder: string }[] = [
  { id: "arxiv", label: "ArXiv", icon: <Search size={14} />, placeholder: "e.g. attention mechanism transformers" },
  { id: "semantic_scholar", label: "Semantic Scholar", icon: <Search size={14} />, placeholder: "e.g. BERT language model" },
  { id: "web_search", label: "Web Search", icon: <Globe size={14} />, placeholder: "e.g. GPT-4 blog posts" },
  { id: "url", label: "URL", icon: <Globe size={14} />, placeholder: "https://..." },
  { id: "pdf", label: "PDF Upload", icon: <FileText size={14} />, placeholder: "" },
];

export function IngestModal({ onClose, onSuccess }: IngestModalProps) {
  const [source, setSource] = useState<IngestionSource>("arxiv");
  const [query, setQuery] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [maxResults, setMaxResults] = useState(10);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedSource = SOURCES.find((s) => s.id === source)!;

  async function handleSubmit() {
    setError(null);
    setLoading(true);
    try {
      if (source === "pdf") {
        if (!file) throw new Error("Please select a PDF file.");
        const result = await ingestPDF(file);
        onSuccess(result.ingested);
      } else {
        const result = await ingestSource({ source, query, max_results: maxResults });
        onSuccess(result.ingested);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ingestion failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-zinc-900 border border-zinc-700 rounded-xl w-full max-w-md shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-zinc-700">
          <h2 className="text-sm font-semibold text-zinc-100">Add to Knowledge Graph</h2>
          <button onClick={onClose} className="text-zinc-400 hover:text-zinc-200">
            <X size={16} />
          </button>
        </div>

        <div className="p-5 space-y-4">
          {/* Source selector */}
          <div>
            <p className="text-xs text-zinc-400 mb-2">Source</p>
            <div className="flex flex-wrap gap-2">
              {SOURCES.map((s) => (
                <button
                  key={s.id}
                  onClick={() => setSource(s.id)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                    source === s.id
                      ? "bg-blue-600 text-white"
                      : "bg-zinc-800 text-zinc-400 hover:text-zinc-200"
                  }`}
                >
                  {s.icon}
                  {s.label}
                </button>
              ))}
            </div>
          </div>

          {/* Input */}
          {source === "pdf" ? (
            <div>
              <p className="text-xs text-zinc-400 mb-2">PDF File</p>
              <label className="flex flex-col items-center justify-center w-full h-24 border-2 border-dashed border-zinc-600 rounded-lg cursor-pointer hover:border-zinc-400 transition-colors">
                <Upload size={20} className="text-zinc-500 mb-1" />
                <span className="text-xs text-zinc-400">
                  {file ? file.name : "Click to upload PDF"}
                </span>
                <input
                  type="file"
                  accept=".pdf"
                  className="hidden"
                  onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                />
              </label>
            </div>
          ) : (
            <>
              <div>
                <p className="text-xs text-zinc-400 mb-2">
                  {source === "url" ? "URL" : "Search Query"}
                </p>
                <Input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder={selectedSource.placeholder}
                  className="bg-zinc-800 border-zinc-600 text-zinc-100 placeholder:text-zinc-500 text-sm"
                  onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
                />
              </div>
              {source !== "url" && (
                <div>
                  <p className="text-xs text-zinc-400 mb-2">Max results: {maxResults}</p>
                  <input
                    type="range"
                    min={1}
                    max={50}
                    value={maxResults}
                    onChange={(e) => setMaxResults(Number(e.target.value))}
                    className="w-full accent-blue-600"
                  />
                </div>
              )}
            </>
          )}

          {error && <p className="text-xs text-red-400">{error}</p>}

          <Button
            onClick={handleSubmit}
            disabled={loading || (source !== "pdf" && !query.trim())}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white text-sm"
          >
            {loading ? "Ingesting…" : "Add to Graph"}
          </Button>
        </div>
      </div>
    </div>
  );
}
