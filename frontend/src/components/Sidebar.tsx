"use client";

import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { PaperCard } from "./PaperCard";
import { searchPapers } from "@/lib/api";
import type { SearchResult } from "@/lib/types";
import { Search, Plus, BookOpen, History, Cpu } from "lucide-react";

interface SidebarProps {
  onPaperSelect: (result: SearchResult) => void;
  onOpenIngest: () => void;
  history: string[];
}

export function Sidebar({ onPaperSelect, onOpenIngest, history }: SidebarProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [tab, setTab] = useState<"search" | "history">("search");

  async function handleSearch(q: string) {
    setQuery(q);
    if (!q.trim()) { setResults([]); return; }
    setLoading(true);
    try {
      const res = await searchPapers(q);
      setResults(res.results);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <aside className="flex flex-col h-full bg-zinc-950 border-r border-zinc-800 w-64 shrink-0">
      {/* Logo */}
      <div className="flex items-center gap-2 px-4 py-4 border-b border-zinc-800">
        <Cpu size={18} className="text-blue-400" />
        <span className="text-sm font-semibold text-zinc-100 tracking-tight">ResearchGraph</span>
      </div>

      {/* Add button */}
      <div className="px-3 pt-3">
        <button
          onClick={onOpenIngest}
          className="flex items-center gap-2 w-full px-3 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium transition-colors"
        >
          <Plus size={14} />
          Add to Knowledge Graph
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 px-3 pt-3">
        {(["search", "history"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors capitalize ${
              tab === t ? "bg-zinc-800 text-zinc-100" : "text-zinc-500 hover:text-zinc-300"
            }`}
          >
            {t === "search" ? <BookOpen size={12} /> : <History size={12} />}
            {t}
          </button>
        ))}
      </div>

      <Separator className="mt-3 bg-zinc-800" />

      {tab === "search" && (
        <>
          <div className="px-3 pt-3 pb-2">
            <div className="relative">
              <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-zinc-500" />
              <Input
                value={query}
                onChange={(e) => handleSearch(e.target.value)}
                placeholder="Search papers…"
                className="pl-8 bg-zinc-900 border-zinc-700 text-zinc-100 placeholder:text-zinc-600 text-xs h-8"
              />
            </div>
          </div>
          <ScrollArea className="flex-1 px-3 pb-3">
            {loading && (
              <p className="text-xs text-zinc-500 text-center mt-4">Searching…</p>
            )}
            {!loading && results.length === 0 && query && (
              <p className="text-xs text-zinc-600 text-center mt-4">No results</p>
            )}
            {!loading && results.length === 0 && !query && (
              <p className="text-xs text-zinc-600 text-center mt-4">
                Search your knowledge graph
              </p>
            )}
            <div className="space-y-2 mt-1">
              {results.map((r) => (
                <PaperCard key={r.id} paper={r} onClick={() => onPaperSelect(r)} />
              ))}
            </div>
          </ScrollArea>
        </>
      )}

      {tab === "history" && (
        <ScrollArea className="flex-1 px-3 py-3">
          {history.length === 0 ? (
            <p className="text-xs text-zinc-600 text-center mt-4">No history yet</p>
          ) : (
            <div className="space-y-1">
              {history.map((msg, i) => (
                <div key={i} className="text-xs text-zinc-400 px-2 py-1.5 rounded-md hover:bg-zinc-800 cursor-pointer line-clamp-2">
                  {msg}
                </div>
              ))}
            </div>
          )}
        </ScrollArea>
      )}
    </aside>
  );
}
