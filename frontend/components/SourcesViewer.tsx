'use client'

import { useState } from 'react'
import { type Source } from '@/lib/api'
import { 
  FileText, 
  ChevronDown, 
  ChevronUp, 
  Layers, 
  BookOpen, 
  Bookmark, 
  Copy, 
  Check 
} from 'lucide-react'

interface SourcesViewerProps {
  sources: Source[]
}

const COLLECTION_THEMES: Record<string, { badge: string; border: string }> = {
  clinical:  { badge: 'bg-rose-50 text-rose-800 border-rose-200', border: 'border-rose-100' },
  nursing:   { badge: 'bg-teal-50 text-teal-800 border-teal-200', border: 'border-teal-100' },
  billing:   { badge: 'bg-amber-50 text-amber-800 border-amber-200', border: 'border-amber-100' },
  equipment: { badge: 'bg-purple-50 text-purple-800 border-purple-200', border: 'border-purple-100' },
  general:   { badge: 'bg-slate-100 text-slate-800 border-slate-200', border: 'border-slate-100' },
}

export default function SourcesViewer({ sources }: SourcesViewerProps) {
  const [isSectionOpen, setIsSectionOpen] = useState(false)
  const [expandedChunks, setExpandedChunks] = useState<Record<number, boolean>>({})
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null)

  if (!sources || sources.length === 0) return null

  function toggleChunk(index: number) {
    setExpandedChunks((prev) => ({
      ...prev,
      [index]: !prev[index],
    }))
  }

  function handleCopy(text: string, index: number) {
    navigator.clipboard.writeText(text)
    setCopiedIdx(index)
    setTimeout(() => setCopiedIdx(null), 2000)
  }

  return (
    <div className="mt-3.5 bg-slate-50/90 border border-slate-200/90 rounded-2xl overflow-hidden shadow-2xs transition-all">
      {/* Collapsible Section Header */}
      <button
        type="button"
        onClick={() => setIsSectionOpen(!isSectionOpen)}
        className={`w-full px-4 py-2.5 flex items-center justify-between bg-slate-100/70 hover:bg-slate-100 transition-colors cursor-pointer text-left group ${
          isSectionOpen ? 'border-b border-slate-200/80' : ''
        }`}
      >
        <div className="flex items-center gap-2">
          <div className="p-1 rounded-md bg-rose-500/10 text-rose-700">
            <Layers className="w-3.5 h-3.5 stroke-[2.5]" />
          </div>
          <span className="text-xs font-bold text-slate-800 tracking-tight">
            Verified Reranked Sources
          </span>
          <span className="text-[11px] font-extrabold px-1.5 py-0.2 rounded-full bg-rose-100 text-rose-800">
            {sources.length} {sources.length === 1 ? 'Chunk' : 'Chunks'}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-[11px] font-semibold text-slate-500 group-hover:text-slate-700">
            {isSectionOpen ? 'Collapse Citations' : 'Expand Citations'}
          </span>
          {isSectionOpen ? (
            <ChevronUp className="w-4 h-4 text-slate-500 group-hover:text-slate-800 transition-transform" />
          ) : (
            <ChevronDown className="w-4 h-4 text-slate-500 group-hover:text-slate-800 transition-transform" />
          )}
        </div>
      </button>

      {/* Expanded Sources Body */}
      {isSectionOpen && (
        <div className="p-3 space-y-2.5">
          {sources.map((src, i) => {
            const isChunkOpen = expandedChunks[i] ?? false
            const theme = COLLECTION_THEMES[src.collection] ?? COLLECTION_THEMES.general
            const hasScore = src.score != null

            return (
              <div
                key={src.id ?? i}
                className="bg-white border border-slate-200/80 rounded-xl overflow-hidden shadow-2xs hover:border-slate-300 transition-all"
              >
                {/* Chunk Card Header */}
                <div
                  onClick={() => toggleChunk(i)}
                  className="p-3 flex items-start justify-between gap-3 cursor-pointer hover:bg-slate-50/70 transition-colors"
                >
                  <div className="flex items-start gap-2.5 min-w-0">
                    <div className="mt-0.5 p-1.5 rounded-lg bg-slate-100 text-slate-600 shrink-0">
                      <FileText className="w-4 h-4" />
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-bold text-slate-900 text-xs truncate max-w-xs sm:max-w-md">
                          {src.document}
                        </span>
                        <span
                          className={`text-[10px] font-extrabold uppercase tracking-wider px-1.5 py-0.5 rounded border ${theme.badge}`}
                        >
                          {src.collection}
                        </span>
                        {src.page_number != null && (
                          <span className="text-[10px] font-semibold text-slate-600 bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200">
                            Page {src.page_number}
                          </span>
                        )}
                      </div>

                      {src.section && (
                        <div className="flex items-center gap-1.5 mt-1 text-slate-600 text-xs">
                          <Bookmark className="w-3 h-3 text-slate-400 shrink-0" />
                          <span className="font-medium truncate">
                            Section: <strong className="font-bold text-slate-800">{src.section}</strong>
                          </span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Reranker Score Badge & Toggle */}
                  <div className="flex items-center gap-2 shrink-0">
                    {hasScore && (
                      <div className="text-right hidden sm:block">
                        <span className="text-[11px] font-mono font-bold text-rose-800 bg-rose-50 border border-rose-200 px-2 py-0.5 rounded-md">
                          CE: {src.score!.toFixed(3)}
                        </span>
                      </div>
                    )}
                    <span className="p-1 rounded hover:bg-slate-200/60 text-slate-400">
                      {isChunkOpen ? (
                        <ChevronUp className="w-4 h-4 text-slate-600" />
                      ) : (
                        <ChevronDown className="w-4 h-4 text-slate-600" />
                      )}
                    </span>
                  </div>
                </div>

                {/* Collapsible Chunk Excerpt Details */}
                {isChunkOpen && (
                  <div className="border-t border-slate-100 bg-slate-50/50 p-3.5 space-y-2 animate-fadeIn">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-extrabold uppercase tracking-wider text-slate-600 flex items-center gap-1">
                        <BookOpen className="w-3 h-3 text-rose-600" />
                        Retrieved Document Excerpt
                      </span>

                      {src.text && (
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation()
                            handleCopy(src.text!, i)
                          }}
                          className="flex items-center gap-1 text-[11px] font-bold text-slate-500 hover:text-rose-700 bg-white border border-slate-200 rounded-md px-2 py-0.5 transition-colors cursor-pointer"
                        >
                          {copiedIdx === i ? (
                            <>
                              <Check className="w-3 h-3 text-emerald-600" />
                              <span className="text-emerald-700">Copied!</span>
                            </>
                          ) : (
                            <>
                              <Copy className="w-3 h-3" />
                              <span>Copy Text</span>
                            </>
                          )}
                        </button>
                      )}
                    </div>

                    {src.text ? (
                      <div className="p-3 bg-white rounded-lg border border-slate-200 text-slate-800 text-xs font-normal leading-relaxed whitespace-pre-wrap font-sans border-l-4 border-l-rose-500">
                        {src.text}
                      </div>
                    ) : (
                      <p className="text-xs text-slate-500 italic">
                        Excerpt text is indexed under section "{src.section}".
                      </p>
                    )}

                    {/* Metadata Footer */}
                    <div className="flex items-center justify-between text-[10px] text-slate-600 pt-1">
                      <span>
                        Document Source: <strong className="font-bold text-slate-700">{src.document}</strong>
                      </span>
                      {hasScore && (
                        <span>
                          CrossEncoder Score: <strong className="font-bold text-rose-700 font-mono">{src.score!.toFixed(4)}</strong>
                        </span>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
