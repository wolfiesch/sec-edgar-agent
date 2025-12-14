import { useState } from 'react';
import { Plus, X, Loader2, TrendingUp, DollarSign, ArrowUpRight, ArrowDownRight, Minus, Download, Copy, Check, BarChart3, LineChart, Table } from 'lucide-react';
import { CompanyComparisonChart } from './TrendChart';

interface CompareCompaniesProps {
  onToast?: (type: 'success' | 'error' | 'info', message: string) => void;
}

interface CompareResult {
  companies: CompanyData[];
  metrics: string[];
  years: number;
  generated_at: string;
}

interface CompanyData {
  ticker: string;
  name: string;
  metrics: Record<string, MetricValue[]>;
}

interface MetricValue {
  year: number;
  value: number | null;
  yoy_change?: number | null;
}

const AVAILABLE_METRICS = [
  { id: 'revenue', label: 'Revenue', icon: DollarSign },
  { id: 'net_income', label: 'Net Income', icon: TrendingUp },
  { id: 'eps', label: 'EPS', icon: DollarSign },
  { id: 'gross_margin', label: 'Gross Margin %', icon: TrendingUp },
  { id: 'operating_margin', label: 'Operating Margin %', icon: TrendingUp },
  { id: 'total_assets', label: 'Total Assets', icon: DollarSign },
  { id: 'total_debt', label: 'Total Debt', icon: DollarSign },
  { id: 'cash', label: 'Cash & Equivalents', icon: DollarSign },
];

const POPULAR_TICKERS = [
  'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'JPM', 'V', 'JNJ',
  'WMT', 'UNH', 'MA', 'PG', 'HD', 'XOM', 'CVX', 'KO', 'PEP', 'ABBV',
];

export function CompareCompanies({ onToast }: CompareCompaniesProps) {
  const [tickers, setTickers] = useState<string[]>(['', '']);
  const [selectedMetrics, setSelectedMetrics] = useState<string[]>(['revenue', 'net_income', 'eps']);
  const [years, setYears] = useState(3);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<CompareResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [viewMode, setViewMode] = useState<'table' | 'chart'>('table');
  const [chartType, setChartType] = useState<'bar' | 'line'>('bar');
  const [chartMetric, setChartMetric] = useState<string>('revenue');

  const handleAddTicker = () => {
    if (tickers.length < 5) {
      setTickers([...tickers, '']);
    }
  };

  const handleRemoveTicker = (index: number) => {
    if (tickers.length > 2) {
      setTickers(tickers.filter((_, i) => i !== index));
    }
  };

  const handleTickerChange = (index: number, value: string) => {
    const updated = [...tickers];
    updated[index] = value.toUpperCase();
    setTickers(updated);
  };

  const handleMetricToggle = (metricId: string) => {
    if (selectedMetrics.includes(metricId)) {
      if (selectedMetrics.length > 1) {
        setSelectedMetrics(selectedMetrics.filter(m => m !== metricId));
      }
    } else {
      setSelectedMetrics([...selectedMetrics, metricId]);
    }
  };

  const handleCompare = async () => {
    const validTickers = tickers.filter(t => t.trim().length > 0);
    if (validTickers.length < 2) {
      setError('Please enter at least 2 tickers to compare');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tickers: validTickers,
          metrics: selectedMetrics,
          years: years,
        }),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Failed to compare companies');
      }

      const data = await response.json();
      setResult(data);
      onToast?.('success', `Compared ${validTickers.length} companies`);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Comparison failed';
      setError(message);
      onToast?.('error', message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopyTable = async () => {
    if (!result) return;
    try {
      const markdown = generateMarkdownTable(result);
      await navigator.clipboard.writeText(markdown);
      setCopied(true);
      onToast?.('success', 'Table copied to clipboard');
      setTimeout(() => setCopied(false), 2000);
    } catch {
      onToast?.('error', 'Failed to copy');
    }
  };

  const handleDownloadCsv = () => {
    if (!result) return;
    try {
      const csv = generateCsv(result);
      const blob = new Blob([csv], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `compare-${result.companies.map(c => c.ticker).join('-')}-${Date.now()}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      onToast?.('success', 'CSV downloaded');
    } catch {
      onToast?.('error', 'Failed to download CSV');
    }
  };

  const isValid = tickers.filter(t => t.trim()).length >= 2 && selectedMetrics.length >= 1;

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="text-center space-y-2">
        <h2 className="text-3xl font-bold text-gray-100">Compare Companies</h2>
        <p className="text-gray-400">
          Side-by-side financial comparison across multiple companies
        </p>
      </div>

      {/* Input Form */}
      <div className="bg-gray-900/50 rounded-xl border border-gray-800 p-6 space-y-6">
        {/* Tickers */}
        <div className="space-y-3">
          <label className="block text-sm font-medium text-gray-300">
            Companies to Compare (2-5)
          </label>
          <div className="flex flex-wrap gap-3">
            {tickers.map((ticker, idx) => (
              <div key={idx} className="relative">
                <input
                  type="text"
                  value={ticker}
                  onChange={(e) => handleTickerChange(idx, e.target.value)}
                  placeholder={`Ticker ${idx + 1}`}
                  className="w-full sm:w-28 px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  list={`ticker-suggestions-${idx}`}
                />
                <datalist id={`ticker-suggestions-${idx}`}>
                  {POPULAR_TICKERS.map(t => (
                    <option key={t} value={t} />
                  ))}
                </datalist>
                {tickers.length > 2 && (
                  <button
                    onClick={() => handleRemoveTicker(idx)}
                    className="absolute -top-2 -right-2 p-1 bg-gray-700 hover:bg-red-600 rounded-full text-gray-400 hover:text-white transition-colors"
                  >
                    <X className="w-3 h-3" />
                  </button>
                )}
              </div>
            ))}
            {tickers.length < 5 && (
              <button
                onClick={handleAddTicker}
                className="w-full sm:w-28 px-3 py-2 border-2 border-dashed border-gray-700 hover:border-gray-500 rounded-lg text-gray-500 hover:text-gray-300 transition-colors flex items-center justify-center gap-1"
              >
                <Plus className="w-4 h-4" />
                Add
              </button>
            )}
          </div>
        </div>

        {/* Metrics Selection */}
        <div className="space-y-3">
          <label className="block text-sm font-medium text-gray-300">
            Metrics to Compare
          </label>
          <div className="flex flex-wrap gap-2">
            {AVAILABLE_METRICS.map((metric) => (
              <button
                key={metric.id}
                onClick={() => handleMetricToggle(metric.id)}
                className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors flex items-center gap-1.5 ${
                  selectedMetrics.includes(metric.id)
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-800 text-gray-400 hover:text-white hover:bg-gray-700 border border-gray-700'
                }`}
              >
                <metric.icon className="w-3.5 h-3.5" />
                {metric.label}
              </button>
            ))}
          </div>
        </div>

        {/* Years Selection */}
        <div className="flex items-center gap-4">
          <label className="text-sm font-medium text-gray-300">
            Historical Years:
          </label>
          <div className="flex gap-2">
            {[1, 3, 5].map((y) => (
              <button
                key={y}
                onClick={() => setYears(y)}
                className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  years === y
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-800 text-gray-400 hover:text-white border border-gray-700'
                }`}
              >
                {y} Year{y > 1 ? 's' : ''}
              </button>
            ))}
          </div>
        </div>

        {/* Compare Button */}
        <button
          onClick={handleCompare}
          disabled={!isValid || isLoading}
          className="w-full py-3 bg-gradient-to-r from-blue-600 to-emerald-600 hover:from-blue-500 hover:to-emerald-500 text-white font-semibold rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Comparing...
            </>
          ) : (
            'Compare Companies'
          )}
        </button>

        {error && (
          <div className="p-3 bg-red-900/50 border border-red-700 rounded-lg text-red-200 text-sm">
            {error}
          </div>
        )}
      </div>

      {/* Results */}
      {result && (
        <div className="bg-gray-900/50 rounded-xl border border-gray-800 p-6 space-y-4">
          {/* Header with View Toggle and Export */}
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div className="flex items-center gap-4">
              <h3 className="text-lg font-semibold text-gray-100">
                Comparison Results
              </h3>
              {/* View Toggle */}
              <div className="flex bg-gray-800 rounded-lg p-0.5">
                <button
                  onClick={() => setViewMode('table')}
                  className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                    viewMode === 'table'
                      ? 'bg-gray-700 text-white'
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  <Table className="w-3.5 h-3.5" />
                  Table
                </button>
                <button
                  onClick={() => setViewMode('chart')}
                  className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                    viewMode === 'chart'
                      ? 'bg-gray-700 text-white'
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  <BarChart3 className="w-3.5 h-3.5" />
                  Chart
                </button>
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleCopyTable}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-md text-gray-300 hover:text-white transition-colors"
              >
                {copied ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-emerald-400" />
                    <span className="text-emerald-400">Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5" />
                    Copy Table
                  </>
                )}
              </button>
              <button
                onClick={handleDownloadCsv}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-md text-gray-300 hover:text-white transition-colors"
              >
                <Download className="w-3.5 h-3.5" />
                CSV
              </button>
            </div>
          </div>

          {/* Chart Controls */}
          {viewMode === 'chart' && (
            <div className="flex items-center gap-4 flex-wrap">
              {/* Metric Selector */}
              <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2">
                <span className="text-sm text-gray-400">Metric:</span>
                <select
                  value={chartMetric}
                  onChange={(e) => setChartMetric(e.target.value)}
                  className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {result.metrics.map((m) => (
                    <option key={m} value={m}>
                      {AVAILABLE_METRICS.find((am) => am.id === m)?.label || m}
                    </option>
                  ))}
                </select>
              </div>
              {/* Chart Type Toggle */}
              <div className="flex bg-gray-800 rounded-lg p-0.5">
                <button
                  onClick={() => setChartType('bar')}
                  className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                    chartType === 'bar'
                      ? 'bg-gray-700 text-white'
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  <BarChart3 className="w-3.5 h-3.5" />
                  Bar
                </button>
                <button
                  onClick={() => setChartType('line')}
                  className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                    chartType === 'line'
                      ? 'bg-gray-700 text-white'
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  <LineChart className="w-3.5 h-3.5" />
                  Line
                </button>
              </div>
            </div>
          )}

          {/* Content: Table or Chart */}
          {viewMode === 'table' ? (
            <div className="overflow-x-auto">
              <ComparisonTable result={result} />
            </div>
          ) : (
            <div className="py-4">
              <CompanyComparisonChart
                companies={result.companies.map((c) => ({
                  ticker: c.ticker,
                  data: c.metrics[chartMetric]?.map((mv) => ({
                    year: mv.year,
                    value: mv.value,
                  })) || [],
                }))}
                metric={chartMetric}
                chartType={chartType}
                height={350}
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ComparisonTable({ result }: { result: CompareResult }) {
  const formatValue = (value: number | null, metric: string): string => {
    if (value === null) return 'N/A';
    if (metric.includes('margin')) return `${value.toFixed(1)}%`;
    if (Math.abs(value) >= 1_000_000_000) return `$${(value / 1_000_000_000).toFixed(1)}B`;
    if (Math.abs(value) >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
    if (metric === 'eps') return `$${value.toFixed(2)}`;
    return `$${value.toLocaleString()}`;
  };

  const formatChange = (change: number | null | undefined) => {
    if (change === null || change === undefined) return null;
    const isPositive = change > 0;
    const isNegative = change < 0;
    return (
      <span className={`text-xs flex items-center ${isPositive ? 'text-emerald-400' : isNegative ? 'text-red-400' : 'text-gray-500'}`}>
        {isPositive ? <ArrowUpRight className="w-3 h-3" /> : isNegative ? <ArrowDownRight className="w-3 h-3" /> : <Minus className="w-3 h-3" />}
        {Math.abs(change).toFixed(1)}%
      </span>
    );
  };

  // Get all years from the data
  const allYears = new Set<number>();
  result.companies.forEach(company => {
    Object.values(company.metrics).forEach(metricValues => {
      metricValues.forEach(mv => allYears.add(mv.year));
    });
  });
  const years = Array.from(allYears).sort((a, b) => b - a);

  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="border-b border-gray-700">
          <th className="text-left py-3 px-4 text-gray-400 font-medium">Metric</th>
          {result.companies.map(company => (
            <th key={company.ticker} className="text-right py-3 px-4 text-gray-200 font-semibold">
              {company.ticker}
              {company.name && (
                <div className="text-xs text-gray-500 font-normal">{company.name}</div>
              )}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {result.metrics.map(metricId => {
          const metricLabel = AVAILABLE_METRICS.find(m => m.id === metricId)?.label || metricId;
          return years.map((year, yearIdx) => (
            <tr key={`${metricId}-${year}`} className={yearIdx === 0 ? 'border-t border-gray-700' : ''}>
              <td className="py-2 px-4 text-gray-300">
                {yearIdx === 0 && <span className="font-medium">{metricLabel}</span>}
                <span className="text-gray-500 ml-2">{year}</span>
              </td>
              {result.companies.map(company => {
                const metricData = company.metrics[metricId]?.find(m => m.year === year);
                return (
                  <td key={`${company.ticker}-${metricId}-${year}`} className="py-2 px-4 text-right">
                    <div className="text-gray-200">{formatValue(metricData?.value ?? null, metricId)}</div>
                    {yearIdx === 0 && formatChange(metricData?.yoy_change)}
                  </td>
                );
              })}
            </tr>
          ));
        })}
      </tbody>
    </table>
  );
}

function generateMarkdownTable(result: CompareResult): string {
  const headers = ['Metric', ...result.companies.map(c => c.ticker)];
  let md = `| ${headers.join(' | ')} |\n`;
  md += `| ${headers.map(() => '---').join(' | ')} |\n`;

  result.metrics.forEach(metricId => {
    const metricLabel = AVAILABLE_METRICS.find(m => m.id === metricId)?.label || metricId;
    const row = [metricLabel];
    result.companies.forEach(company => {
      const latest = company.metrics[metricId]?.[0];
      row.push(latest?.value?.toLocaleString() ?? 'N/A');
    });
    md += `| ${row.join(' | ')} |\n`;
  });

  return md;
}

function generateCsv(result: CompareResult): string {
  const headers = ['Metric', 'Year', ...result.companies.map(c => c.ticker)];
  let csv = headers.join(',') + '\n';

  result.metrics.forEach(metricId => {
    const metricLabel = AVAILABLE_METRICS.find(m => m.id === metricId)?.label || metricId;
    // Get all years
    const allYears = new Set<number>();
    result.companies.forEach(company => {
      company.metrics[metricId]?.forEach(mv => allYears.add(mv.year));
    });
    Array.from(allYears).sort((a, b) => b - a).forEach(year => {
      const row = [metricLabel, year.toString()];
      result.companies.forEach(company => {
        const data = company.metrics[metricId]?.find(m => m.year === year);
        row.push(data?.value?.toString() ?? '');
      });
      csv += row.join(',') + '\n';
    });
  });

  return csv;
}
