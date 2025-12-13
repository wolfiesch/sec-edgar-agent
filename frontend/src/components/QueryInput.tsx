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

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (value.trim() && !isLoading) {
      onSubmit(value);
    }
  };

  const handleClear = () => {
    setValue('');
    if (onReset) onReset();
  };

  const handleExampleClick = (query: string) => {
    if (!isLoading) {
      setValue(query);
      onSubmit(query);
    }
  };

  return (
    <div className="w-full max-w-3xl mx-auto space-y-4">
      <form onSubmit={handleSubmit} className="relative">
        <input
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="Ask about companies, filings, or financial data..."
          className="w-full px-6 py-4 text-lg bg-gray-800 border border-gray-700 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent pl-14 pr-24 text-white placeholder-gray-400 shadow-lg transition-all"
          disabled={isLoading}
        />
        <Search className="absolute left-5 top-1/2 transform -translate-y-1/2 text-gray-400 w-6 h-6" />

        <div className="absolute right-3 top-1/2 transform -translate-y-1/2 flex items-center gap-2">
          {hasResult && !isLoading && (
            <button
              type="button"
              onClick={handleClear}
              className="p-2 text-gray-400 hover:text-white transition-colors"
              title="Clear and Reset"
            >
              <X className="w-5 h-5" />
            </button>
          )}
          <button
            type="submit"
            disabled={!value.trim() || isLoading}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-full font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Thinking...' : 'Go'}
          </button>
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
