"use client";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Paper, SearchResult } from "@/lib/types";
import { ExternalLink } from "lucide-react";

interface PaperCardProps {
  paper: Paper | SearchResult;
  onClick?: () => void;
}

function isPaper(p: Paper | SearchResult): p is Paper {
  return "abstract" in p;
}

export function PaperCard({ paper, onClick }: PaperCardProps) {
  const title = paper.title;
  const snippet = isPaper(paper) ? paper.abstract : paper.snippet;
  const url = paper.url;
  const source = isPaper(paper)
    ? paper.source
    : (paper.metadata?.source as string | undefined);
  const date = isPaper(paper)
    ? paper.published_date
    : (paper.metadata?.published_date as string | undefined);

  return (
    <Card
      className="cursor-pointer bg-zinc-900 border-zinc-700 hover:border-zinc-500 transition-colors"
      onClick={onClick}
    >
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-zinc-100 leading-snug line-clamp-2">
          {title}
        </CardTitle>
        <div className="flex items-center gap-2 flex-wrap">
          {source && (
            <Badge variant="outline" className="text-xs text-zinc-400 border-zinc-600 capitalize">
              {source}
            </Badge>
          )}
          {date && (
            <span className="text-xs text-zinc-500">{date.slice(0, 10)}</span>
          )}
        </div>
      </CardHeader>
      {snippet && (
        <CardContent className="pb-3">
          <p className="text-xs text-zinc-400 line-clamp-3">{snippet}</p>
          {url && (
            <a
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-2 inline-flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300"
              onClick={(e) => e.stopPropagation()}
            >
              <ExternalLink size={10} />
              Open
            </a>
          )}
        </CardContent>
      )}
    </Card>
  );
}
