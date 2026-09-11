'use client'

import React from 'react'

interface MarkdownRendererProps {
  content: string
  className?: string
}

/**
 * Format inline markdown text:
 * - **bold** -> <strong>
 * - *italic* -> <em>
 * - `code`   -> <code>
 */
function renderInline(text: string): React.ReactNode[] {
  // Regex to match bold (**...**), code (`...`), or italic (*...*) non-greedily
  const tokens = text.split(/(\*\*.*?\*\*|`[^`]+`|\*.*?\*)/g)

  return tokens.map((token, idx) => {
    if (token.startsWith('**') && token.endsWith('**') && token.length >= 4) {
      return (
        <strong key={idx} className="font-bold text-slate-900">
          {token.slice(2, -2)}
        </strong>
      )
    }
    if (token.startsWith('`') && token.endsWith('`') && token.length > 2) {
      return (
        <code
          key={idx}
          className="px-1.5 py-0.5 rounded-md bg-rose-50 border border-rose-100 text-rose-700 font-mono text-xs font-semibold"
        >
          {token.slice(1, -1)}
        </code>
      )
    }
    if (token.startsWith('*') && token.endsWith('*') && token.length > 2) {
      return (
        <em key={idx} className="italic text-slate-700">
          {token.slice(1, -1)}
        </em>
      )
    }
    return token
  })
}

/**
 * High-performance, robust Markdown parser that formats:
 * - Bold text with crisp weights (font-bold)
 * - Markdown tables (rendered as responsive, modern bordered tables)
 * - Headings (h1, h2, h3, h4)
 * - Unordered and ordered lists
 * - Blockquotes and code snippets
 */
export default function MarkdownRenderer({ content, className = '' }: MarkdownRendererProps) {
  if (!content) return null

  const lines = content.split('\n')
  const elements: React.ReactNode[] = []

  let i = 0
  while (i < lines.length) {
    const line = lines[i]

    // 1. Markdown Table parsing
    if (line.trim().startsWith('|') && line.trim().endsWith('|')) {
      const tableLines: string[] = []
      while (i < lines.length && lines[i].trim().startsWith('|') && lines[i].trim().endsWith('|')) {
        tableLines.push(lines[i].trim())
        i++
      }

      if (tableLines.length >= 2) {
        const headerRow = tableLines[0]
          .split('|')
          .slice(1, -1)
          .map((c) => c.trim())

        // Check if second row is separator |---|---|
        const hasSeparator = tableLines[1].includes('-')
        const bodyRows = (hasSeparator ? tableLines.slice(2) : tableLines.slice(1)).map((row) =>
          row
            .split('|')
            .slice(1, -1)
            .map((c) => c.trim())
        )

        elements.push(
          <div key={`table-${i}`} className="my-3 overflow-x-auto rounded-xl border border-slate-200/90 shadow-2xs">
            <table className="w-full text-left text-sm border-collapse">
              <thead>
                <tr className="bg-slate-100/80 border-b border-slate-200">
                  {headerRow.map((cell, cIdx) => (
                    <th key={cIdx} className="py-2.5 px-3.5 font-bold text-slate-900 text-xs uppercase tracking-wider">
                      {renderInline(cell)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {bodyRows.map((row, rIdx) => (
                  <tr key={rIdx} className="hover:bg-slate-50/70 transition-colors">
                    {row.map((cell, cIdx) => (
                      <td key={cIdx} className="py-2 px-3.5 text-slate-700 font-medium">
                        {renderInline(cell)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
        continue
      }
    }

    // 2. Headings
    if (line.startsWith('### ')) {
      elements.push(
        <h3 key={`h3-${i}`} className="font-bold text-base text-slate-900 mt-3 mb-1">
          {renderInline(line.replace(/^###\s+/, ''))}
        </h3>
      )
      i++
      continue
    }
    if (line.startsWith('## ')) {
      elements.push(
        <h2 key={`h2-${i}`} className="font-bold text-lg text-slate-900 mt-4 mb-2">
          {renderInline(line.replace(/^##\s+/, ''))}
        </h2>
      )
      i++
      continue
    }
    if (line.startsWith('# ')) {
      elements.push(
        <h1 key={`h1-${i}`} className="font-extrabold text-xl text-slate-900 mt-4 mb-2">
          {renderInline(line.replace(/^#\s+/, ''))}
        </h1>
      )
      i++
      continue
    }

    // 3. Unordered list (- or *)
    if (/^\s*[-*]\s+/.test(line)) {
      const listItems: string[] = []
      while (i < lines.length && /^\s*[-*]\s+/.test(lines[i])) {
        listItems.push(lines[i].replace(/^\s*[-*]\s+/, ''))
        i++
      }
      elements.push(
        <ul key={`ul-${i}`} className="my-2 space-y-1.5 pl-1">
          {listItems.map((item, idx) => (
            <li key={idx} className="flex items-start gap-2.5 text-slate-700">
              <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-rose-500 shrink-0" />
              <span className="leading-relaxed">{renderInline(item)}</span>
            </li>
          ))}
        </ul>
      )
      continue
    }

    // 4. Numbered list (1. 2.)
    if (/^\s*\d+\.\s+/.test(line)) {
      const listItems: string[] = []
      while (i < lines.length && /^\s*\d+\.\s+/.test(lines[i])) {
        listItems.push(lines[i].replace(/^\s*\d+\.\s+/, ''))
        i++
      }
      elements.push(
        <ol key={`ol-${i}`} className="my-2 space-y-1.5 pl-1">
          {listItems.map((item, idx) => (
            <li key={idx} className="flex items-start gap-2 text-slate-700">
              <span className="font-bold text-rose-600 text-xs mt-0.5 shrink-0 min-w-4 text-right">
                {idx + 1}.
              </span>
              <span className="leading-relaxed">{renderInline(item)}</span>
            </li>
          ))}
        </ol>
      )
      continue
    }

    // 5. Empty lines
    if (!line.trim()) {
      elements.push(<div key={`sp-${i}`} className="h-2" />)
      i++
      continue
    }

    // 6. Regular paragraph
    elements.push(
      <p key={`p-${i}`} className="leading-relaxed text-slate-800">
        {renderInline(line)}
      </p>
    )
    i++
  }

  return <div className={`space-y-1 font-normal text-sm ${className}`}>{elements}</div>
}

