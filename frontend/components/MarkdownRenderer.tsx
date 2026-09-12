"use client";

import React from "react";
import { CitationItem } from "@/lib/api";
import { ExternalLink, ChevronRight, BookOpen, Quote } from "lucide-react";

interface MarkdownRendererProps {
  content: string;
  citations?: CitationItem[];
  onOpenCitation?: (citation: CitationItem) => void;
}

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({
  content,
  citations = [],
  onOpenCitation,
}) => {
  if (!content) return null;

  // Helper to parse inline tokens: bold, italic, code, and footnote citations
  const parseInline = (text: string): React.ReactNode[] => {
    // Regex matching:
    // 1. Footnotes: [^1] or [1]
    // 2. Bold: **text**
    // 3. Italic: *text* or _text_
    // 4. Inline code: `code`
    const regex = /(\[\^[0-9]+\]|\[[0-9]+\]|\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g;
    const parts = text.split(regex);

    return parts.map((part, idx) => {
      if (!part) return null;

      // 1. Footnote Citation [^1] or [1]
      const footnoteMatch = part.match(/^\[\^?([0-9]+)\]$/);
      if (footnoteMatch) {
        const citationNum = parseInt(footnoteMatch[1], 10);
        const citationObj = citations[citationNum - 1];

        return (
          <button
            key={`fn-${idx}`}
            onClick={() => citationObj && onOpenCitation?.(citationObj)}
            className="inline-flex items-center gap-1 mx-1 px-2.5 py-0.5 rounded-full text-[11px] font-extrabold bg-[#DEEED9] text-[#2D5A27] border border-[#7FB53D]/40 hover:bg-[#7FB53D] hover:text-white transition-all shadow-xs align-baseline cursor-pointer group"
            title={
              citationObj
                ? `${citationObj.instrument_name} ${citationObj.section_number ? `Section ${citationObj.section_number}` : ""}`
                : `Citation [${citationNum}]`
            }
          >
            <span>[{citationNum}]</span>
            <ExternalLink className="w-2.5 h-2.5 text-[#2D5A27] group-hover:text-white" />
          </button>
        );
      }

      // 2. Bold text **text**
      const boldMatch = part.match(/^\*\*([^*]+)\*\*$/);
      if (boldMatch) {
        return (
          <strong key={`bold-${idx}`} className="font-extrabold text-[#1E2D24]">
            {boldMatch[1]}
          </strong>
        );
      }

      // 3. Italic text *text*
      const italicMatch = part.match(/^\*([^*]+)\*$/);
      if (italicMatch) {
        return (
          <em key={`italic-${idx}`} className="italic text-[#2D5A27] font-medium">
            {italicMatch[1]}
          </em>
        );
      }

      // 4. Inline Code `code`
      const codeMatch = part.match(/^`([^`]+)`$/);
      if (codeMatch) {
        return (
          <code
            key={`code-${idx}`}
            className="px-1.5 py-0.5 rounded-md bg-[#DEEED9] text-[#2D5A27] font-mono text-xs border border-[#7FB53D]/25"
          >
            {codeMatch[1]}
          </code>
        );
      }

      // Regular text
      return <span key={`txt-${idx}`}>{part}</span>;
    });
  };

  // Split lines and process block-level structures
  const lines = content.split("\n");
  const renderedBlocks: React.ReactNode[] = [];

  let inOrderedList = false;
  let inUnorderedList = false;
  let currentListItems: React.ReactNode[] = [];
  let inTable = false;
  let tableHeader: string[] = [];
  let tableRows: string[][] = [];

  const flushList = (keyPrefix: number) => {
    if (inOrderedList && currentListItems.length > 0) {
      renderedBlocks.push(
        <ol key={`ol-${keyPrefix}`} className="space-y-3 my-3 pl-1">
          {currentListItems}
        </ol>
      );
      currentListItems = [];
      inOrderedList = false;
    } else if (inUnorderedList && currentListItems.length > 0) {
      renderedBlocks.push(
        <ul key={`ul-${keyPrefix}`} className="space-y-2 my-3 pl-1">
          {currentListItems}
        </ul>
      );
      currentListItems = [];
      inUnorderedList = false;
    }
  };

  const flushTable = (keyPrefix: number) => {
    if (inTable && (tableHeader.length > 0 || tableRows.length > 0)) {
      renderedBlocks.push(
        <div
          key={`table-${keyPrefix}`}
          className="my-3.5 overflow-x-auto rounded-xl border border-[#D8EADB] bg-white print:border-gray-300 print:my-2.5 print:break-inside-avoid shadow-2xs"
        >
          <table className="w-full text-xs text-left border-collapse">
            {tableHeader.length > 0 && (
              <thead>
                <tr className="bg-[#F3FFFB] border-b border-[#D8EADB] print:bg-gray-100 print:border-gray-300">
                  {tableHeader.map((h, i) => (
                    <th
                      key={i}
                      className="px-3.5 py-2.5 font-bold text-[#2D5A27] print:text-gray-900 border-r border-[#D8EADB]/60 last:border-r-0"
                    >
                      {parseInline(h)}
                    </th>
                  ))}
                </tr>
              </thead>
            )}
            <tbody className="divide-y divide-[#D8EADB]/50 print:divide-gray-200">
              {tableRows.map((row, rIdx) => (
                <tr
                  key={rIdx}
                  className={rIdx % 2 === 0 ? "bg-white" : "bg-[#F3FFFB]/30 print:bg-gray-50/60"}
                >
                  {row.map((cell, cIdx) => (
                    <td
                      key={cIdx}
                      className="px-3.5 py-2 text-[#1E2D24] border-r border-[#D8EADB]/40 last:border-r-0 leading-relaxed"
                    >
                      {parseInline(cell)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
      tableHeader = [];
      tableRows = [];
      inTable = false;
    }
  };

  const flushAll = (keyPrefix: number) => {
    flushList(keyPrefix);
    flushTable(keyPrefix);
  };

  lines.forEach((line, index) => {
    const trimmed = line.trim();

    // Blank line
    if (!trimmed) {
      flushAll(index);
      return;
    }

    // Markdown Horizontal Rule (---, ***, ___)
    if (/^(\-{3,}|\*{3,}|_{3,})$/.test(trimmed)) {
      flushAll(index);
      renderedBlocks.push(
        <hr
          key={`hr-${index}`}
          className="my-4 border-t border-[#D8EADB] print:border-gray-300"
        />
      );
      return;
    }

    // Markdown Table Row (| col1 | col2 |)
    if (trimmed.startsWith("|") && trimmed.endsWith("|")) {
      flushList(index);
      const cells = trimmed
        .slice(1, -1)
        .split("|")
        .map((c) => c.trim());

      // Check if it is a separator row (|---|---|)
      const isSeparator = cells.every((c) => /^:?-+:?$/.test(c));
      if (isSeparator) {
        // Just marks that the preceding row was the table header
        return;
      }

      if (!inTable) {
        inTable = true;
        tableHeader = cells;
      } else {
        tableRows.push(cells);
      }
      return;
    }

    // If not a table row, flush any open table
    if (inTable) {
      flushTable(index);
    }

    // Heading #, ##, ###
    if (trimmed.startsWith("### ")) {
      flushList(index);
      renderedBlocks.push(
        <h4
          key={`h4-${index}`}
          className="text-base sm:text-lg font-serif-luxury font-bold text-[#1E2D24] mt-5 mb-2 flex items-center gap-2 print:text-black print:mt-3"
        >
          <span className="w-2 h-2 rounded-full bg-[#7FB53D] print:hidden" />
          {parseInline(trimmed.replace(/^###\s+/, ""))}
        </h4>
      );
      return;
    }

    if (trimmed.startsWith("## ")) {
      flushList(index);
      renderedBlocks.push(
        <h3
          key={`h3-${index}`}
          className="text-lg sm:text-xl font-serif-luxury font-bold text-[#1E2D24] mt-6 mb-3 border-b border-[#DEEED9] pb-1.5 print:text-black print:border-gray-300 print:mt-4"
        >
          {parseInline(trimmed.replace(/^##\s+/, ""))}
        </h3>
      );
      return;
    }

    if (trimmed.startsWith("# ")) {
      flushList(index);
      renderedBlocks.push(
        <h2
          key={`h2-${index}`}
          className="text-xl sm:text-2xl font-serif-luxury font-bold text-[#1E2D24] mt-7 mb-3.5 border-b-2 border-[#7FB53D] pb-2 print:text-black print:border-gray-400 print:mt-4"
        >
          {parseInline(trimmed.replace(/^#\s+/, ""))}
        </h2>
      );
      return;
    }

    // Standalone Section Titles like **Analysis:** or **Explanation:**
    const standaloneHeaderMatch = trimmed.match(/^\*\*([A-Za-z0-9\s:_-]+)\*\*$/);
    if (standaloneHeaderMatch) {
      flushList(index);
      renderedBlocks.push(
        <div key={`section-h-${index}`} className="mt-4 mb-2 print:my-2">
          <span className="text-xs sm:text-sm font-extrabold uppercase tracking-wider text-[#2D5A27] bg-[#DEEED9] px-3 py-1 rounded-full border border-[#7FB53D]/30 inline-flex items-center gap-1.5 shadow-2xs print:border-gray-300 print:bg-gray-100 print:text-black">
            <span className="w-1.5 h-1.5 rounded-full bg-[#7FB53D] print:hidden" />
            {standaloneHeaderMatch[1]}
          </span>
        </div>
      );
      return;
    }

    // Blockquote > quote
    if (trimmed.startsWith("> ")) {
      flushList(index);
      renderedBlocks.push(
        <div
          key={`quote-${index}`}
          className="parchment-box p-4 rounded-2xl my-3.5 text-xs sm:text-sm leading-relaxed border-l-4 border-[#7FB53D] text-[#2D5A27] italic shadow-xs print:bg-gray-50 print:border-gray-400 print:text-gray-900 print:my-2"
        >
          {parseInline(trimmed.replace(/^>\s+/, ""))}
        </div>
      );
      return;
    }

    // Numbered List: 1. or 2.
    const numberedMatch = trimmed.match(/^([0-9]+)\.\s+(.*)$/);
    if (numberedMatch) {
      if (inUnorderedList) flushList(index);
      inOrderedList = true;
      const num = numberedMatch[1];
      const itemText = numberedMatch[2];

      currentListItems.push(
        <li key={`ol-item-${index}`} className="flex items-start gap-2.5">
          <span className="w-5 h-5 rounded-full bg-[#DEEED9] text-[#2D5A27] text-xs font-extrabold flex items-center justify-center shrink-0 mt-0.5 border border-[#7FB53D]/30 shadow-2xs print:border-gray-300 print:bg-gray-100 print:text-black">
            {num}
          </span>
          <div className="flex-1 text-xs sm:text-sm leading-relaxed text-[#1E2D24]">
            {parseInline(itemText)}
          </div>
        </li>
      );
      return;
    }

    // Bullet List: - or *
    const bulletMatch = trimmed.match(/^[-*•]\s+(.*)$/);
    if (bulletMatch) {
      if (inOrderedList) flushList(index);
      inUnorderedList = true;
      const itemText = bulletMatch[1];

      currentListItems.push(
        <li key={`ul-item-${index}`} className="flex items-start gap-2.5 pl-2">
          <span className="w-1.5 h-1.5 rounded-full bg-[#7FB53D] shrink-0 mt-2 print:bg-gray-700" />
          <div className="flex-1 text-xs sm:text-sm leading-relaxed text-[#1E2D24]">
            {parseInline(itemText)}
          </div>
        </li>
      );
      return;
    }

    // Regular Paragraph
    flushList(index);
    renderedBlocks.push(
      <p
        key={`p-${index}`}
        className="text-xs sm:text-sm text-[#1E2D24] leading-relaxed my-2.5 print:my-1.5"
      >
        {parseInline(trimmed)}
      </p>
    );
  });

  flushAll(lines.length);

  return <div className="space-y-1">{renderedBlocks}</div>;
};
