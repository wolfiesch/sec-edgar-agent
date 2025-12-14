import { useState } from 'react';
import { Loader2, AlertTriangle, Plus, Minus, RefreshCw, ArrowRight, FileText, ChevronDown, ChevronUp } from 'lucide-react';

interface FilingDiffProps {
  onToast?: (type: 'success' | 'error' | 'info', message: string) => void;
}

interface DiffResult {
  success: boolean;
  ticker: string;
  comparison: {
    year1: {
      fiscal_year: number;
      filing_date: string;
      accession: string;
    };
    year2: {
      fiscal_year: number;
      filing_date: string;
      accession: string;
    };
  };
  changes: {
    new_risks: string[];
    removed_risks: string[];
    modified_risks: Array<{
      similarity: number;
      before: string;
      after: string;
    }>;
    unchanged_count: number;
    summary: {
      total_year1: number;
      total_year2: number;
      new_count: number;
      removed_count: number;
      modified_count: number;
    };
  };
  narrative: string;
  error?: string;
}

const CURRENT_YEAR = new Date().getFullYear();
const YEARS = Array.from({ length: 10 }, (_, i) => CURRENT_YEAR - i);

export function FilingDiff({ onToast }: FilingDiffProps) {
  const [ticker, setTicker] = useState('');
  const [year1, setYear1] = useState(CURRENT_YEAR - 2);
  const [year2, setYear2] = useState(CURRENT_YEAR - 1);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<DiffResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['new', 'removed', 'modified']));

  const toggleSection = (section: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(section)) {
      newExpanded.delete(section);
    } else {
      newExpanded.add(section);
    }
    setExpandedSections(newExpanded);
  };

  const handleCompare = async () => {
    if (!ticker.trim()) {
      setError('Please enter a ticker symbol');
      return;
    }

    if (year1 >= year2) {
      setError('Year 1 must be earlier than Year 2');
      return;
    }

    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch('/api/v1/filings/diff', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ticker: ticker.toUpperCase(),
          year1,
          year2,
        }),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Failed to compare filings');
      }

      const data = await response.json();
      setResult(data);

      if (data.success) {
        const summary = data.changes?.summary;
        if (summary) {
          const totalChanges = summary.new_count + summary.removed_count + summary.modified_count;
          onToast?.('success', `Found ${totalChanges} change${totalChanges !== 1 ? 's' : ''} in risk factors`);
        }
      } else {
        setError(data.error || 'No changes detected');
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Comparison failed';
      setError(message);
      onToast?.('error', message);
    } finally {
      setIsLoading(false);
    }
  };

  const isValid = ticker.trim().length > 0 && year1 < year2;

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div className="text-center space-y-2">
        <h2 className="text-3xl font-bold text-gray-100">Filing Change Detection</h2>
        <p className="text-gray-400">
          Compare risk factors between two annual filings to identify changes
        </p>
      </div>

      {/* Input Form */}
      <div className="bg-gray-900/50 rounded-xl border border-gray-800 p-6 space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Ticker */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-300">Ticker</label>
            <input
              type="text"
              value={ticker}
              onChange={(e) => setTicker(e.target.value.toUpperCase())}
              placeholder="AAPL"
              className="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Year 1 */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-300">From Year</label>
            <select
              value={year1}
              onChange={(e) => setYear1(Number(e.target.value))}
              className="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {YEARS.map((y) => (
                <option key={y} value={y}>{y}</option>
              ))}
            </select>
          </div>

          {/* Arrow */}
          <div className="hidden md:flex items-end justify-center pb-3">
            <ArrowRight className="w-6 h-6 text-gray-500" />
          </div>

          {/* Year 2 */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-300">To Year</label>
            <select
              value={year2}
              onChange={(e) => setYear2(Number(e.target.value))}
              className="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {YEARS.map((y) => (
                <option key={y} value={y}>{y}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Compare Button */}
        <button
          onClick={handleCompare}
          disabled={!isValid || isLoading}
          className="w-full py-3 bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 text-white font-semibold rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Analyzing Risk Factors...
            </>
          ) : (
            <>
              <RefreshCw className="w-5 h-5" />
              Detect Changes
            </>
          )}
        </button>

        {error && (
          <div className="p-3 bg-red-900/50 border border-red-700 rounded-lg text-red-200 text-sm flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
            {error}
          </div>
        )}
      </div>

      {/* Results */}
      {result && result.success && result.changes && (
        <div className="space-y-6">
          {/* Summary Card */}
          <div className="bg-gray-900/50 rounded-xl border border-gray-800 p-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-100 flex items-center gap-2">
                  <FileText className="w-5 h-5" />
                  {result.ticker} Risk Factor Changes
                </h3>
                <p className="text-sm text-gray-400 mt-1">
                  {result.comparison.year1.fiscal_year} → {result.comparison.year2.fiscal_year}
                </p>
              </div>
              <div className="grid grid-cols-3 gap-4 text-center">
                <div className="bg-emerald-900/30 border border-emerald-700/50 rounded-lg px-2 py-1 sm:px-4 sm:py-2">
                  <div className="text-2xl font-bold text-emerald-400">{result.changes.summary.new_count}</div>
                  <div className="text-xs text-emerald-300">Added</div>
                </div>
                <div className="bg-red-900/30 border border-red-700/50 rounded-lg px-2 py-1 sm:px-4 sm:py-2">
                  <div className="text-2xl font-bold text-red-400">{result.changes.summary.removed_count}</div>
                  <div className="text-xs text-red-300">Removed</div>
                </div>
                <div className="bg-amber-900/30 border border-amber-700/50 rounded-lg px-2 py-1 sm:px-4 sm:py-2">
                  <div className="text-2xl font-bold text-amber-400">{result.changes.summary.modified_count}</div>
                  <div className="text-xs text-amber-300">Modified</div>
                </div>
              </div>
            </div>

            {/* Narrative */}
            <p className="text-gray-300 text-sm bg-gray-800/50 rounded-lg p-4">
              {result.narrative}
            </p>
          </div>

          {/* New Risks */}
          {result.changes.new_risks.length > 0 && (
            <div className="bg-gray-900/50 rounded-xl border border-gray-800 overflow-hidden">
              <button
                onClick={() => toggleSection('new')}
                className="w-full p-4 flex items-center justify-between hover:bg-gray-800/50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-emerald-900/50 rounded-lg">
                    <Plus className="w-4 h-4 text-emerald-400" />
                  </div>
                  <span className="font-medium text-gray-100">
                    New Risks Added ({result.changes.new_risks.length})
                  </span>
                </div>
                {expandedSections.has('new') ? (
                  <ChevronUp className="w-5 h-5 text-gray-400" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-gray-400" />
                )}
              </button>
              {expandedSections.has('new') && (
                <div className="border-t border-gray-800 p-4 space-y-3">
                  {result.changes.new_risks.map((risk, idx) => (
                    <div key={idx} className="p-3 bg-emerald-900/20 border-l-4 border-emerald-500 rounded-r-lg">
                      <p className="text-sm text-gray-300">{risk}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Removed Risks */}
          {result.changes.removed_risks.length > 0 && (
            <div className="bg-gray-900/50 rounded-xl border border-gray-800 overflow-hidden">
              <button
                onClick={() => toggleSection('removed')}
                className="w-full p-4 flex items-center justify-between hover:bg-gray-800/50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-red-900/50 rounded-lg">
                    <Minus className="w-4 h-4 text-red-400" />
                  </div>
                  <span className="font-medium text-gray-100">
                    Risks Removed ({result.changes.removed_risks.length})
                  </span>
                </div>
                {expandedSections.has('removed') ? (
                  <ChevronUp className="w-5 h-5 text-gray-400" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-gray-400" />
                )}
              </button>
              {expandedSections.has('removed') && (
                <div className="border-t border-gray-800 p-4 space-y-3">
                  {result.changes.removed_risks.map((risk, idx) => (
                    <div key={idx} className="p-3 bg-red-900/20 border-l-4 border-red-500 rounded-r-lg">
                      <p className="text-sm text-gray-300 line-through opacity-75">{risk}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Modified Risks */}
          {result.changes.modified_risks.length > 0 && (
            <div className="bg-gray-900/50 rounded-xl border border-gray-800 overflow-hidden">
              <button
                onClick={() => toggleSection('modified')}
                className="w-full p-4 flex items-center justify-between hover:bg-gray-800/50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-amber-900/50 rounded-lg">
                    <RefreshCw className="w-4 h-4 text-amber-400" />
                  </div>
                  <span className="font-medium text-gray-100">
                    Modified Risks ({result.changes.modified_risks.length})
                  </span>
                </div>
                {expandedSections.has('modified') ? (
                  <ChevronUp className="w-5 h-5 text-gray-400" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-gray-400" />
                )}
              </button>
              {expandedSections.has('modified') && (
                <div className="border-t border-gray-800 p-4 space-y-4">
                  {result.changes.modified_risks.map((mod, idx) => (
                    <div key={idx} className="space-y-2">
                      <div className="flex items-center gap-2 text-xs text-gray-500">
                        <span>Similarity: {(mod.similarity * 100).toFixed(0)}%</span>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <div className="p-3 bg-red-900/10 border border-red-900/30 rounded-lg">
                          <div className="text-xs text-red-400 mb-1 font-medium">Before</div>
                          <p className="text-sm text-gray-400">{mod.before}</p>
                        </div>
                        <div className="p-3 bg-emerald-900/10 border border-emerald-900/30 rounded-lg">
                          <div className="text-xs text-emerald-400 mb-1 font-medium">After</div>
                          <p className="text-sm text-gray-300">{mod.after}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* No Changes */}
          {result.changes.unchanged_count > 0 && (
            <div className="text-center text-sm text-gray-500">
              {result.changes.unchanged_count} risk factor{result.changes.unchanged_count !== 1 ? 's' : ''} remained unchanged
            </div>
          )}
        </div>
      )}
    </div>
  );
}
