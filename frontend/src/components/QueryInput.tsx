import React, { useState } from 'react';
import { Search, X, Sparkles } from 'lucide-react';

interface QueryInputProps {
  onSubmit: (query: string) => void;
  isLoading: boolean;
  onReset?: () => void;
  hasResult?: boolean;
}

const EXAMPLE_QUERIES = [
  { label: "Apple's revenue", query: "What was Apple's total revenue in fiscal year 2024?" },
  { label: "NVIDIA risk factors", query: "What are NVIDIA's main risk factors related to China?" },
  { label: "Compare MSFT & GOOG", query: "Compare Microsoft and Google's net income for the past 3 years" },
  { label: "Tesla insider trades", query: "Show me recent insider trading activity for Tesla" },
  { label: "Meta's cash flow", query: "What was Meta's operating cash flow in 2024?" },
];

export function QueryInput({ onSubmit, isLoading, onReset, hasResult }: QueryInputProps) {
  const [value, setValue] = useState('');
  const textareaRef = React.useRef<HTMLTextAreaElement>(null);

  const submitQuery = () => {
    if (value.trim() && !isLoading) {
      onSubmit(value);
      // Reset height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    submitQuery();
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submitQuery();
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setValue(e.target.value);
    // Auto-resize
    e.target.style.height = 'auto';
    e.target.style.height = `${e.target.scrollHeight}px`;
  };

  const handleClear = () => {
    setValue('');
    if (onReset) onReset();
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleExampleClick = (query: string) => {
    if (!isLoading) {
      setValue(query);
      onSubmit(query);
    }
  };

  return (
    <div className="w-full max-w-3xl mx-auto space-y-6 transition-all duration-500 ease-out">
      <form onSubmit={handleSubmit} className="relative group">
        <div className={`absolute -inset-1 bg-gradient-to-r from-sky-500 to-emerald-500 rounded-2xl blur opacity-25 group-hover:opacity-50 transition duration-1000 group-hover:duration-200 ${isLoading ? 'animate-pulse' : ''}`}></div>
        <div className="relative">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            placeholder="Ask about companies, filings, or financial data..."
            rows={1}
            className="w-full px-6 py-4 pl-14 pr-24 text-lg bg-slate-900/90 border border-slate-700/50 rounded-2xl focus:outline-none focus:ring-2 focus:ring-sky-500/50 focus:border-transparent text-slate-100 placeholder-slate-400 shadow-xl backdrop-blur-xl resize-none min-h-[60px] max-h-[200px] overflow-y-auto scrollbar-hide"
            disabled={isLoading}
          />
          <Search className="absolute left-5 top-5 text-slate-400 w-6 h-6" />

          <div className="absolute right-3 top-3 flex items-center gap-2">
            {hasResult && !isLoading && (
              <button
                type="button"
                onClick={handleClear}
                className="p-2 text-slate-400 hover:text-white transition-colors bg-slate-800/50 hover:bg-slate-700/50 rounded-lg backdrop-blur-sm"
                title="Clear and Reset"
              >
                <X className="w-5 h-5" />
              </button>
            )}
            <button
              type="submit"
              disabled={!value.trim() || isLoading}
              className="bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white px-4 py-2 rounded-xl font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-sky-500/20 active:scale-95 flex items-center gap-2 h-10"
            >
              {isLoading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Thinking</span>
                </>
              ) : 'Ask'}
            </button>
          </div>
        </div>
      </form>

      {/* Example queries - only show when no result */}
      {!hasResult && !isLoading && (
        <div className="flex flex-wrap items-center justify-center gap-2">
          <span className="text-gray-500 text-sm flex items-center gap-1">
            <Sparkles className="w-3.5 h-3.5" />
            Try:
          </span>
          {EXAMPLE_QUERIES.map((example, idx) => (
            <button
              key={idx}
              onClick={() => handleExampleClick(example.query)}
              className="px-3 py-1.5 text-sm bg-gray-800/50 hover:bg-gray-700 border border-gray-700 hover:border-gray-600 rounded-full text-gray-300 hover:text-white transition-all"
              title={example.query}
            >
              {example.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
