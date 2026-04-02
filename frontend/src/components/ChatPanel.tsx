"use client";

import { useEffect, useRef, useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { PaperCard } from "./PaperCard";
import { streamChat } from "@/lib/api";
import type { ChatMessage, SearchResult } from "@/lib/types";
import { Send, Bot, User, Loader2 } from "lucide-react";

const INTENT_LABELS: Record<string, string> = {
  qa: "Q&A",
  summarize: "Summary",
  discover: "Discovery",
  ingest: "Ingest",
  search: "Search",
};

const INTENT_COLORS: Record<string, string> = {
  qa: "bg-blue-600/20 text-blue-300 border-blue-600/30",
  summarize: "bg-purple-600/20 text-purple-300 border-purple-600/30",
  discover: "bg-emerald-600/20 text-emerald-300 border-emerald-600/30",
  ingest: "bg-amber-600/20 text-amber-300 border-amber-600/30",
  search: "bg-zinc-600/20 text-zinc-300 border-zinc-600/30",
};

interface ChatPanelProps {
  contextPaperIds?: string[];
  onHistoryUpdate: (msg: string) => void;
}

export function ChatPanel({ contextPaperIds = [], onHistoryUpdate }: ChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend() {
    const text = input.trim();
    if (!text || streaming) return;
    setInput("");

    const userMsg: ChatMessage = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    onHistoryUpdate(text);

    const assistantMsg: ChatMessage = { role: "assistant", content: "", intent: "qa" };
    setMessages((prev) => [...prev, assistantMsg]);
    setStreaming(true);

    const history = messages.map((m) => ({ role: m.role, content: m.content }));

    await streamChat(
      { message: text, history, context_paper_ids: contextPaperIds },
      (token) => {
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last.role === "assistant") {
            updated[updated.length - 1] = { ...last, content: last.content + token };
          }
          return updated;
        });
      },
      (intent) => {
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last.role === "assistant") {
            updated[updated.length - 1] = { ...last, intent };
          }
          return updated;
        });
        setStreaming(false);
      },
      (err) => {
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last.role === "assistant") {
            updated[updated.length - 1] = { ...last, content: `Error: ${err.message}` };
          }
          return updated;
        });
        setStreaming(false);
      },
    );
  }

  return (
    <div className="flex flex-col h-full bg-zinc-950">
      {/* Header */}
      <div className="flex items-center gap-2 px-5 py-3.5 border-b border-zinc-800">
        <Bot size={16} className="text-blue-400" />
        <span className="text-sm font-medium text-zinc-200">Research Assistant</span>
        {streaming && <Loader2 size={13} className="ml-auto animate-spin text-zinc-500" />}
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1 px-4 py-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center py-20">
            <Bot size={32} className="text-zinc-700 mb-3" />
            <p className="text-sm text-zinc-400 font-medium">Ask anything about your research</p>
            <p className="text-xs text-zinc-600 mt-1">
              Try: &ldquo;Summarize attention mechanism papers&rdquo; or &ldquo;Find connections between BERT and GPT&rdquo;
            </p>
          </div>
        )}
        <div className="space-y-5 max-w-3xl mx-auto">
          {messages.map((msg, i) => (
            <div key={i} className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              {msg.role === "assistant" && (
                <div className="w-7 h-7 rounded-full bg-blue-600/20 border border-blue-600/30 flex items-center justify-center shrink-0 mt-0.5">
                  <Bot size={14} className="text-blue-400" />
                </div>
              )}
              <div className={`max-w-[75%] ${msg.role === "user" ? "items-end" : "items-start"} flex flex-col gap-1`}>
                {msg.role === "assistant" && msg.intent && (
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium border ${INTENT_COLORS[msg.intent] ?? INTENT_COLORS.qa}`}>
                    {INTENT_LABELS[msg.intent] ?? msg.intent}
                  </span>
                )}
                <div
                  className={`rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                    msg.role === "user"
                      ? "bg-blue-600 text-white rounded-tr-sm"
                      : "bg-zinc-800/80 text-zinc-200 rounded-tl-sm"
                  }`}
                >
                  {msg.content || (msg.role === "assistant" && streaming && i === messages.length - 1 ? (
                    <span className="inline-flex gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-zinc-500 animate-bounce [animation-delay:0ms]" />
                      <span className="w-1.5 h-1.5 rounded-full bg-zinc-500 animate-bounce [animation-delay:150ms]" />
                      <span className="w-1.5 h-1.5 rounded-full bg-zinc-500 animate-bounce [animation-delay:300ms]" />
                    </span>
                  ) : null)}
                </div>
              </div>
              {msg.role === "user" && (
                <div className="w-7 h-7 rounded-full bg-zinc-700 flex items-center justify-center shrink-0 mt-0.5">
                  <User size={14} className="text-zinc-300" />
                </div>
              )}
            </div>
          ))}
        </div>
        <div ref={bottomRef} />
      </ScrollArea>

      {/* Input */}
      <div className="px-4 py-3 border-t border-zinc-800">
        <div className="flex gap-2 max-w-3xl mx-auto">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
            placeholder="Ask about your research…"
            disabled={streaming}
            className="bg-zinc-900 border-zinc-700 text-zinc-100 placeholder:text-zinc-600 text-sm"
          />
          <Button
            onClick={handleSend}
            disabled={streaming || !input.trim()}
            size="icon"
            className="bg-blue-600 hover:bg-blue-700 text-white shrink-0"
          >
            <Send size={15} />
          </Button>
        </div>
        <p className="text-[10px] text-zinc-600 text-center mt-1.5">
          Tip: &ldquo;summarize&rdquo;, &ldquo;find connections&rdquo;, &ldquo;search for&rdquo;
        </p>
      </div>
    </div>
  );
}
