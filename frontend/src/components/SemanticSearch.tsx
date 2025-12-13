import { useState } from 'react';
import { SecClient, type SearchResponse, type SearchResult } from '../services/api';
import { Loader2, Search, FileText, ChevronDown, ChevronUp } from 'lucide-react';

export function SemanticSearch() {
  const [query, setQuery] = useState('');
  const [ticker, setTicker] = useState('');
  const [limit, setLimit] = useState(5);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [expandedResults, setExpandedResults] = useState<Set<number>>(new Set());

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setResults(null);
    setExpandedResults(new Set());

    try {
      const data = await SecClient.searchSemantic({
        query: query.trim(),
        ticker: ticker.trim() || undefined,
        limit,
      });
      setResults(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const toggleExpand = (index: number) => {
    const newExpanded = new Set(expandedResults);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedResults(newExpanded);
  };

  const exampleQueries = [
    'risk factors mentioning supply chain disruptions',
    'artificial intelligence and machine learning investments',
    'cybersecurity threats and data breaches',
    'climate change risks and sustainability',
    'revenue recognition policies',
  ];

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-8">
      <div className="space-y-4 text-center">
        <h2 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-pink-400">
          Semantic Search
        </h2>
        <p className="text-gray-400 max-w-2xl mx-auto">
          Search SEC filings using natural language. Find relevant sections across all indexed documents.
        </p>
      </div>

      {/* Search Form */}
      <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-6 backdrop-blur-sm space-y-4">
        <form onSubmit={handleSearch} className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-300">Search Query</label>
            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="w-full bg-gray-950 border border-gray-700 rounded-lg pl-12 pr-4 py-3 text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none"
                placeholder="e.g., risk factors related to China supply chain"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-300">Filter by Ticker (optional)</label>
              <input
                type="text"
                value={ticker}
                onChange={(e) => setTicker(e.target.value.toUpperCase())}
                className="w-full bg-gray-950 border border-gray-700 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none"
                placeholder="AAPL"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-300">Results Limit</label>
              <select
                value={limit}
                onChange={(e) => setLimit(parseInt(e.target.value))}
                className="w-full bg-gray-950 border border-gray-700 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none"
              >
                <option value={3}>3 results</option>
                <option value={5}>5 results</option>
                <option value={10}>10 results</option>
                <option value={20}>20 results</option>
              </select>
            </div>
            <div className="flex items-end">
              <button
                type="submit"
                disabled={loading || !query.trim()}
                className="w-full bg-purple-600 hover:bg-purple-500 text-white font-medium py-2 px-6 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                Search
              </button>
            </div>
          </div>
        </form>

        {/* Example Queries */}
        <div className="pt-4 border-t border-gray-800">
          <p className="text-xs text-gray-500 mb-2">Try an example:</p>
          <div className="flex flex-wrap gap-2">
            {exampleQueries.map((eq, i) => (
              <button
                key={i}
                onClick={() => setQuery(eq)}
                className="text-xs px-3 py-1 bg-gray-800 hover:bg-gray-700 text-gray-400 hover:text-gray-200 rounded-full transition-colors"
              >
                {eq}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-lg">
          {error}
        </div>
      )}

      {/* Results */}
      {results && (
        <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-200">
              Found {results.total} result{results.total !== 1 ? 's' : ''}
            </h3>
          </div>

          <div className="space-y-3">
            {results.results.map((result, index) => (
              <SearchResultCard
                key={index}
                result={result}
                isExpanded={expandedResults.has(index)}
                onToggle={() => toggleExpand(index)}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function SearchResultCard({
  result,
  isExpanded,
  onToggle,
}: {
  result: SearchResult;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  const previewLength = 200;
  const needsExpand = result.content.length > previewLength;
  const displayContent = isExpanded
    ? result.content
    : result.content.slice(0, previewLength) + (needsExpand ? '...' : '');

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 bg-gray-800/50 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-purple-400" />
          <span className="font-mono text-sm text-purple-400">{result.citation}</span>
        </div>
        {result.distance !== undefined && (
          <span className="text-xs text-gray-500">
            Score: {(1 - result.distance).toFixed(3)}
          </span>
        )}
      </div>

      {/* Content */}
      <div className="p-4">
        <p className="text-gray-300 text-sm whitespace-pre-wrap">{displayContent}</p>

        {needsExpand && (
          <button
            onClick={onToggle}
            className="mt-3 text-xs text-purple-400 hover:text-purple-300 flex items-center gap-1"
          >
            {isExpanded ? (
              <>
                <ChevronUp className="w-3 h-3" /> Show less
              </>
            ) : (
              <>
                <ChevronDown className="w-3 h-3" /> Show more
              </>
            )}
          </button>
        )}
      </div>
    </div>
  );
}
