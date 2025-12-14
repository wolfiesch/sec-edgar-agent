import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Components } from 'react-markdown';
import { ExternalLink, FileText, Loader2, Copy, Download, Check } from 'lucide-react';
import { useState } from 'react';

interface ResponsePanelProps {
  content: string | null;
  isProcessing: boolean;
  onToast?: (type: 'success' | 'error' | 'info', message: string) => void;
}

/**
 * Transform citation patterns like [AAPL 10-K 2024] into clickable SEC links
 */
function processCitations(text: string): string {
  // Pattern: [TICKER FORM YEAR] or [TICKER FORM YEAR, Section]
  const citationPattern = /\[([A-Z]{1,5})\s+(10-[KQ]|8-K|Form\s*4)\s+(\d{4})(?:,\s*([^\]]+))?\]/g;

  return text.replace(citationPattern, (_match, ticker, form, year, section) => {
    // Build SEC EDGAR search URL
    const formType = form.replace(/\s+/g, '').toLowerCase();
    const secUrl = `https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&company=${ticker}&type=${formType}&dateb=&owner=include&count=40&search_text=`;
    const sectionInfo = section ? `, ${section}` : '';
    return `[${ticker} ${form} ${year}${sectionInfo}](${secUrl})`;
  });
}

// Custom components for better markdown rendering
const markdownComponents: Components = {
  // Enhanced table styling
  table: ({ children }) => (
    <div className="overflow-x-auto my-6 rounded-xl border border-slate-700/50 shadow-sm">
      <table className="min-w-full divide-y divide-slate-700/50">
        {children}
      </table>
    </div>
  ),
  thead: ({ children }) => (
    <thead className="bg-slate-800/80 backdrop-blur-sm">
      {children}
    </thead>
  ),
  th: ({ children }) => (
    <th className="px-6 py-4 text-left text-xs font-bold text-slate-300 uppercase tracking-wider">
      {children}
    </th>
  ),
  td: ({ children }) => (
    <td className="px-6 py-4 text-sm text-slate-300 border-t border-slate-700/30 whitespace-pre-wrap">
      {children}
    </td>
  ),
  tr: ({ children }) => (
    <tr className="hover:bg-slate-800/30 transition-colors odd:bg-slate-900/20 even:bg-transparent">
      {children}
    </tr>
  ),
  // Enhanced link styling (for citations)
  a: ({ href, children }) => {
    const isSecLink = href?.includes('sec.gov');
    return (
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        className={`inline-flex items-center gap-1.5 transition-all
          ${isSecLink 
            ? 'bg-sky-900/30 text-sky-300 px-2 py-0.5 rounded-md text-sm font-medium hover:bg-sky-900/50 hover:text-sky-200 border border-sky-800/30' 
            : 'text-sky-400 hover:text-sky-300 underline decoration-sky-400/50 hover:decoration-sky-300'
          }`}
      >
        {isSecLink && <FileText className="w-3.5 h-3.5" />}
        {children}
        {!isSecLink && <ExternalLink className="w-3 h-3 inline opacity-70" />}
      </a>
    );
  },
  // Code block styling
  code: ({ className, children }) => {
    const isInline = !className;
    if (isInline) {
      return (
        <code className="bg-slate-800/80 text-emerald-400 px-1.5 py-0.5 rounded text-sm font-mono border border-slate-700/50">
          {children}
        </code>
      );
    }
    return (
      <code className={`${className} block bg-slate-950 p-6 rounded-xl overflow-x-auto text-sm border border-slate-800 shadow-inner font-mono my-4`}>
        {children}
      </code>
    );
  },
  // List styling
  ul: ({ children }) => (
    <ul className="list-disc list-outside space-y-2 my-4 ml-4 text-slate-300 marker:text-sky-500">
      {children}
    </ul>
  ),
  ol: ({ children }) => (
    <ol className="list-decimal list-outside space-y-2 my-4 ml-4 text-slate-300 marker:text-sky-500 font-medium">
      {children}
    </ol>
  ),
  // Heading styling
  h1: ({ children }) => (
    <h1 className="text-3xl font-extrabold text-white mt-10 mb-6 pb-4 border-b border-slate-700/50 bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">
      {children}
    </h1>
  ),
  h2: ({ children }) => (
    <h2 className="text-2xl font-bold text-slate-100 mt-8 mb-4 flex items-center gap-3">
      <span className="w-2 h-8 rounded-full bg-sky-500 inline-block"></span>
      {children}
    </h2>
  ),
  h3: ({ children }) => (
    <h3 className="text-lg font-semibold text-slate-200 mt-6 mb-3">
      {children}
    </h3>
  ),
  // Paragraph styling
  p: ({ children }) => (
    <p className="text-slate-300 leading-relaxed my-4 text-base">
      {children}
    </p>
  ),
  // Strong/bold styling
  strong: ({ children }) => (
    <strong className="font-bold text-slate-100">
      {children}
    </strong>
  ),
  // Blockquote styling
  blockquote: ({ children }) => (
    <blockquote className="border-l-4 border-sky-500/50 pl-6 py-2 my-6 text-slate-400 italic bg-slate-900/30 rounded-r-lg">
      {children}
    </blockquote>
  ),
  hr: () => (
    <hr className="my-8 border-slate-700/50" />
  )
};

export function ResponsePanel({ content, isProcessing, onToast }: ResponsePanelProps) {
  const [copiedMarkdown, setCopiedMarkdown] = useState(false);

  const handleCopyMarkdown = async () => {
    if (!content) return;
    try {
      await navigator.clipboard.writeText(content);
      setCopiedMarkdown(true);
      onToast?.('success', 'Copied to clipboard');
      setTimeout(() => setCopiedMarkdown(false), 2000);
    } catch {
      onToast?.('error', 'Failed to copy to clipboard');
    }
  };

  const handleDownloadJson = () => {
    if (!content) return;
    try {
      // Extract structured data from the markdown content
      const jsonData = {
        content: content,
        exportedAt: new Date().toISOString(),
        format: 'markdown',
        citations: extractCitations(content),
      };
      const blob = new Blob([JSON.stringify(jsonData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `sec-agent-response-${Date.now()}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      onToast?.('success', 'JSON downloaded');
    } catch {
      onToast?.('error', 'Failed to download JSON');
    }
  };

  if (!content) {
    if (isProcessing) {
      return (
        <div className="h-full flex flex-col items-center justify-center text-gray-400 gap-3">
          <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
          <span className="text-sm">Analyzing SEC filings...</span>
        </div>
      );
    }
    return (
      <div className="h-full flex flex-col items-center justify-center text-gray-500 gap-2">
        <FileText className="w-12 h-12 text-gray-600" />
        <span>Ready to research.</span>
        <span className="text-xs text-gray-600">Ask about any public company's SEC filings</span>
      </div>
    );
  }

  // Process citations to make them clickable
  const processedContent = processCitations(content);

  return (
    <div className="relative">
      {/* Export Buttons */}
      <div className="absolute top-3 right-3 flex items-center gap-2 z-10">
        <button
          onClick={handleCopyMarkdown}
          className="flex items-center gap-1.5 p-2 sm:px-3 sm:py-1.5 text-xs font-medium bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-md text-gray-300 hover:text-white transition-colors"
          title="Copy as Markdown"
        >
          {copiedMarkdown ? (
            <>
              <Check className="w-3.5 h-3.5 text-emerald-400" />
              <span className="hidden sm:inline text-emerald-400">Copied!</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Copy MD</span>
            </>
          )}
        </button>
        <button
          onClick={handleDownloadJson}
          className="flex items-center gap-1.5 p-2 sm:px-3 sm:py-1.5 text-xs font-medium bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-md text-gray-300 hover:text-white transition-colors"
          title="Download as JSON"
        >
          <Download className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">JSON</span>
        </button>
      </div>

      <div className="p-6 pt-12 overflow-y-auto max-h-[400px] lg:max-h-[600px] custom-scrollbar">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={markdownComponents}
        >
          {processedContent}
        </ReactMarkdown>
      </div>
    </div>
  );
}

/**
 * Extract citations from content for JSON export
 */
function extractCitations(text: string): Array<{ ticker: string; form: string; year: string; section?: string }> {
  const citationPattern = /\[([A-Z]{1,5})\s+(10-[KQ]|8-K|Form\s*4)\s+(\d{4})(?:,\s*([^\]]+))?\]/g;
  const citations: Array<{ ticker: string; form: string; year: string; section?: string }> = [];
  let match;

  while ((match = citationPattern.exec(text)) !== null) {
    citations.push({
      ticker: match[1],
      form: match[2],
      year: match[3],
      section: match[4] || undefined,
    });
  }

  return citations;
}
