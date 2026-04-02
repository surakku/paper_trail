"use client";

import { useState } from "react";
import { Sidebar } from "@/components/Sidebar";
import { ChatPanel } from "@/components/ChatPanel";
import { GraphPanel } from "@/components/GraphPanel";
import { IngestModal } from "@/components/IngestModal";
import type { SearchResult } from "@/lib/types";

export default function Home() {
  const [showIngest, setShowIngest] = useState(false);
  const [contextPaperIds, setContextPaperIds] = useState<string[]>([]);
  const [chatHistory, setChatHistory] = useState<string[]>([]);
  const [graphKey, setGraphKey] = useState(0);

  function handlePaperSelect(result: SearchResult) {
    setContextPaperIds((prev) =>
      prev.includes(result.id) ? prev : [...prev, result.id].slice(-5)
    );
  }

  function handleIngestSuccess(_count: number) {
    setShowIngest(false);
    setGraphKey((k) => k + 1);
  }

  return (
    <div className="flex h-screen overflow-hidden bg-zinc-950">
      <Sidebar
        onPaperSelect={handlePaperSelect}
        onOpenIngest={() => setShowIngest(true)}
        history={chatHistory}
      />

      <main className="flex-1 min-w-0">
        <ChatPanel
          contextPaperIds={contextPaperIds}
          onHistoryUpdate={(msg) => setChatHistory((prev) => [msg, ...prev].slice(0, 50))}
        />
      </main>

      <aside className="w-80 shrink-0">
        <GraphPanel key={graphKey} />
      </aside>

      {showIngest && (
        <IngestModal
          onClose={() => setShowIngest(false)}
          onSuccess={handleIngestSuccess}
        />
      )}
    </div>
  );
}
