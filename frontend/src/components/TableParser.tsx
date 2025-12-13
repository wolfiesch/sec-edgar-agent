
import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { SecClient, type ParsedTableResponse } from '../services/api';
import { Loader2, Table as TableIcon, FileText } from 'lucide-react';
import clsx from 'clsx';

export function TableParser() {
  const [ticker, setTicker] = useState('AAPL');
  const [formType, setFormType] = useState('10-K');
  const [year, setYear] = useState('2024');
  const [tableName, setTableName] = useState('income_statement');

  const tableTypes = [
    { value: 'income_statement', label: 'Income Statement' },
    { value: 'balance_sheet', label: 'Balance Sheet' },
    { value: 'cash_flow', label: 'Cash Flow Statement' },
    { value: 'segment_information', label: 'Segment Information' },
  ];
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ParsedTableResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'markdown' | 'json'>('markdown');

  const handleParse = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await SecClient.parseTable({
        ticker,
        form_type: formType,
        year: parseInt(year),
        table_name: tableName,
      });
      setResult(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-8">
      <div className="space-y-4 text-center">
        <h2 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400">
          SEC Table Parser
        </h2>
        <p className="text-gray-400 max-w-2xl mx-auto">
          Extract structured data from SEC filings with 100% accuracy using Inline XBRL.
        </p>
      </div>

      {/* Input Form */}
      <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-6 backdrop-blur-sm">
        <form onSubmit={handleParse} className="grid grid-cols-1 md:grid-cols-6 gap-4 items-end">
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-300">Ticker</label>
            <input
              type="text"
              value={ticker}
              onChange={(e) => setTicker(e.target.value.toUpperCase())}
              className="w-full bg-gray-950 border border-gray-700 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
              placeholder="AAPL"
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-300">Form Type</label>
            <select
              value={formType}
              onChange={(e) => setFormType(e.target.value)}
              className="w-full bg-gray-950 border border-gray-700 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
            >
              <option value="10-K">10-K</option>
              <option value="10-Q">10-Q</option>
              <option value="8-K">8-K</option>
            </select>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-300">Year</label>
            <input
              type="number"
              value={year}
              onChange={(e) => setYear(e.target.value)}
              className="w-full bg-gray-950 border border-gray-700 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-300">Table Type</label>
            <select
              value={tableName}
              onChange={(e) => setTableName(e.target.value)}
              className="w-full bg-gray-950 border border-gray-700 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
            >
              {tableTypes.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </div>
          <button
            type="submit"
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-500 text-white font-medium py-2 px-6 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <TableIcon className="w-4 h-4" />}
            Parse
          </button>
        </form>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-lg">
          {error}
        </div>
      )}

      {/* Result Display */}
      {result && (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4">
          {/* Citation Banner */}
          <div className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 p-4 rounded-lg flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4" />
              <span className="font-mono text-sm">{result.citation}</span>
            </div>
            <div className="text-sm text-emerald-500/70">
              Confidence: {result.confidence}
            </div>
          </div>

          {/* View Toggle */}
          <div className="flex gap-2 border-b border-gray-800">
            <button
              onClick={() => setViewMode('markdown')}
              className={clsx(
                "px-4 py-2 text-sm font-medium transition-colors border-b-2",
                viewMode === 'markdown' 
                  ? "border-blue-500 text-blue-400" 
                  : "border-transparent text-gray-400 hover:text-gray-200"
              )}
            >
              Markdown View
            </button>
            <button
              onClick={() => setViewMode('json')}
              className={clsx(
                "px-4 py-2 text-sm font-medium transition-colors border-b-2",
                viewMode === 'json' 
                  ? "border-blue-500 text-blue-400" 
                  : "border-transparent text-gray-400 hover:text-gray-200"
              )}
            >
              Raw JSON
            </button>
          </div>

          {/* Content Area */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 overflow-hidden">
            {viewMode === 'markdown' ? (
              <div className="prose prose-invert max-w-none prose-table:border-collapse prose-th:bg-gray-800 prose-th:p-2 prose-td:p-2 prose-td:border prose-td:border-gray-700">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {result.markdown}
                </ReactMarkdown>
              </div>
            ) : (
              <pre className="text-xs font-mono text-gray-300 overflow-auto max-h-[600px] p-4 bg-gray-950 rounded-lg">
                {JSON.stringify(result.structured, null, 2)}
              </pre>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
