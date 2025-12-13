import React, { useState, useRef, useEffect, useCallback } from 'react';
import { ChevronDown, TrendingUp, AlertTriangle, DollarSign, FileText, History } from 'lucide-react';

interface QuickActionsProps {
  onSubmit: (query: string) => void;
  isLoading: boolean;
}

// Top 60 companies by market cap for autocomplete
const POPULAR_TICKERS: { ticker: string; name: string }[] = [
  { ticker: 'AAPL', name: 'Apple Inc.' },
  { ticker: 'MSFT', name: 'Microsoft Corporation' },
  { ticker: 'GOOGL', name: 'Alphabet Inc. (Google)' },
  { ticker: 'AMZN', name: 'Amazon.com Inc.' },
  { ticker: 'NVDA', name: 'NVIDIA Corporation' },
  { ticker: 'META', name: 'Meta Platforms Inc.' },
  { ticker: 'TSLA', name: 'Tesla Inc.' },
  { ticker: 'BRK.B', name: 'Berkshire Hathaway Inc.' },
  { ticker: 'JPM', name: 'JPMorgan Chase & Co.' },
  { ticker: 'V', name: 'Visa Inc.' },
  { ticker: 'JNJ', name: 'Johnson & Johnson' },
  { ticker: 'WMT', name: 'Walmart Inc.' },
  { ticker: 'UNH', name: 'UnitedHealth Group' },
  { ticker: 'MA', name: 'Mastercard Inc.' },
  { ticker: 'PG', name: 'Procter & Gamble' },
  { ticker: 'HD', name: 'The Home Depot' },
  { ticker: 'XOM', name: 'Exxon Mobil Corporation' },
  { ticker: 'CVX', name: 'Chevron Corporation' },
  { ticker: 'KO', name: 'The Coca-Cola Company' },
  { ticker: 'PEP', name: 'PepsiCo Inc.' },
  { ticker: 'ABBV', name: 'AbbVie Inc.' },
  { ticker: 'MRK', name: 'Merck & Co.' },
  { ticker: 'LLY', name: 'Eli Lilly and Company' },
  { ticker: 'AVGO', name: 'Broadcom Inc.' },
  { ticker: 'PFE', name: 'Pfizer Inc.' },
  { ticker: 'TMO', name: 'Thermo Fisher Scientific' },
  { ticker: 'COST', name: 'Costco Wholesale' },
  { ticker: 'CSCO', name: 'Cisco Systems' },
  { ticker: 'ABT', name: 'Abbott Laboratories' },
  { ticker: 'CRM', name: 'Salesforce Inc.' },
  { ticker: 'ORCL', name: 'Oracle Corporation' },
  { ticker: 'ACN', name: 'Accenture plc' },
  { ticker: 'NKE', name: 'Nike Inc.' },
  { ticker: 'MCD', name: 'McDonald\'s Corporation' },
  { ticker: 'DIS', name: 'The Walt Disney Company' },
  { ticker: 'AMD', name: 'Advanced Micro Devices' },
  { ticker: 'INTC', name: 'Intel Corporation' },
  { ticker: 'ADBE', name: 'Adobe Inc.' },
  { ticker: 'NFLX', name: 'Netflix Inc.' },
  { ticker: 'QCOM', name: 'Qualcomm Inc.' },
  { ticker: 'TXN', name: 'Texas Instruments' },
  { ticker: 'INTU', name: 'Intuit Inc.' },
  { ticker: 'HON', name: 'Honeywell International' },
  { ticker: 'IBM', name: 'IBM Corporation' },
  { ticker: 'BA', name: 'The Boeing Company' },
  { ticker: 'CAT', name: 'Caterpillar Inc.' },
  { ticker: 'GE', name: 'General Electric' },
  { ticker: 'GS', name: 'Goldman Sachs Group' },
  { ticker: 'MS', name: 'Morgan Stanley' },
  { ticker: 'AXP', name: 'American Express' },
  { ticker: 'BLK', name: 'BlackRock Inc.' },
  { ticker: 'SBUX', name: 'Starbucks Corporation' },
  { ticker: 'NOW', name: 'ServiceNow Inc.' },
  { ticker: 'PYPL', name: 'PayPal Holdings' },
  { ticker: 'SQ', name: 'Block Inc. (Square)' },
  { ticker: 'UBER', name: 'Uber Technologies' },
  { ticker: 'ABNB', name: 'Airbnb Inc.' },
  { ticker: 'ZM', name: 'Zoom Video Communications' },
  { ticker: 'COP', name: 'ConocoPhillips' },
  { ticker: 'F', name: 'Ford Motor Company' },
];

const QUICK_ACTIONS = [
  {
    label: '📊 Financial Overview',
    query: 'Give me a financial overview of {ticker} including revenue, net income, and key metrics',
    icon: DollarSign,
    color: 'from-blue-500 to-cyan-500'
  },
  {
    label: '⚠️ Risk Factors',
    query: 'What are the key risk factors disclosed in {ticker}\'s latest 10-K filing?',
    icon: AlertTriangle,
    color: 'from-amber-500 to-orange-500'
  },
  {
    label: '📈 Revenue Trends',
    query: 'Show me {ticker}\'s revenue trends over the past 3 years with YoY growth',
    icon: TrendingUp,
    color: 'from-emerald-500 to-green-500'
  },
  {
    label: '📋 10-K Summary',
    query: 'Summarize the key highlights from {ticker}\'s latest 10-K annual report',
    icon: FileText,
    color: 'from-purple-500 to-pink-500'
  },
];

const RECENT_TICKERS_KEY = 'sec_agent_recent_tickers';
const MAX_RECENT_TICKERS = 5;

export function QuickActions({ onSubmit, isLoading }: QuickActionsProps) {
  const [ticker, setTicker] = useState('');
  const [showDropdown, setShowDropdown] = useState(false);
  const [filteredTickers, setFilteredTickers] = useState(POPULAR_TICKERS.slice(0, 10));
  const [recentTickers, setRecentTickers] = useState<string[]>([]);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Load recent tickers from localStorage
  useEffect(() => {
    const stored = localStorage.getItem(RECENT_TICKERS_KEY);
    if (stored) {
      try {
        setRecentTickers(JSON.parse(stored));
      } catch {
        // Invalid JSON, ignore
      }
    }
  }, []);

  // Save ticker to recent list
  const saveRecentTicker = useCallback((t: string) => {
    const upper = t.toUpperCase();
    setRecentTickers(prev => {
      const filtered = prev.filter(r => r !== upper);
      const updated = [upper, ...filtered].slice(0, MAX_RECENT_TICKERS);
      localStorage.setItem(RECENT_TICKERS_KEY, JSON.stringify(updated));
      return updated;
    });
  }, []);

  // Filter tickers based on input
  useEffect(() => {
    if (!ticker) {
      // Show recent tickers first, then popular ones
      const recentSet = new Set(recentTickers);
      const recentItems = recentTickers
        .map(t => POPULAR_TICKERS.find(p => p.ticker === t))
        .filter(Boolean) as typeof POPULAR_TICKERS;
      const otherItems = POPULAR_TICKERS.filter(p => !recentSet.has(p.ticker)).slice(0, 10 - recentItems.length);
      setFilteredTickers([...recentItems, ...otherItems]);
    } else {
      const searchTerm = ticker.toUpperCase();
      const matches = POPULAR_TICKERS.filter(
        t => t.ticker.includes(searchTerm) || t.name.toLowerCase().includes(ticker.toLowerCase())
      ).slice(0, 10);
      setFilteredTickers(matches);
    }
    setHighlightedIndex(-1);
  }, [ticker, recentTickers]);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleTickerSelect = (t: string) => {
    setTicker(t);
    setShowDropdown(false);
    inputRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!showDropdown) return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setHighlightedIndex(prev => Math.min(prev + 1, filteredTickers.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setHighlightedIndex(prev => Math.max(prev - 1, -1));
    } else if (e.key === 'Enter' && highlightedIndex >= 0) {
      e.preventDefault();
      handleTickerSelect(filteredTickers[highlightedIndex].ticker);
    } else if (e.key === 'Escape') {
      setShowDropdown(false);
    }
  };

  const handleQuickAction = (queryTemplate: string) => {
    if (!ticker.trim() || isLoading) return;
    const finalQuery = queryTemplate.replace('{ticker}', ticker.toUpperCase());
    saveRecentTicker(ticker);
    onSubmit(finalQuery);
  };

  const isTickerValid = ticker.trim().length > 0;

  return (
    <div className="w-full max-w-3xl mx-auto space-y-4">
      {/* Ticker Input with Autocomplete */}
      <div className="relative" ref={dropdownRef}>
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-400 whitespace-nowrap">Select company:</span>
          <div className="relative flex-1 max-w-xs">
            <input
              ref={inputRef}
              type="text"
              value={ticker}
              onChange={(e) => {
                setTicker(e.target.value.toUpperCase());
                setShowDropdown(true);
              }}
              onFocus={() => setShowDropdown(true)}
              onKeyDown={handleKeyDown}
              placeholder="AAPL, MSFT, GOOGL..."
              className="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-white placeholder-gray-500 pr-10"
              disabled={isLoading}
            />
            <button
              type="button"
              onClick={() => setShowDropdown(!showDropdown)}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-gray-400 hover:text-gray-200"
            >
              <ChevronDown className={`w-4 h-4 transition-transform ${showDropdown ? 'rotate-180' : ''}`} />
            </button>
          </div>
          {recentTickers.length > 0 && !ticker && (
            <div className="flex items-center gap-2">
              <History className="w-3.5 h-3.5 text-gray-500" />
              <div className="flex gap-1.5">
                {recentTickers.slice(0, 3).map(t => (
                  <button
                    key={t}
                    onClick={() => handleTickerSelect(t)}
                    className="px-2 py-1 text-xs bg-gray-800/50 hover:bg-gray-700 border border-gray-700 rounded text-gray-300 hover:text-white transition-colors"
                  >
                    {t}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Autocomplete Dropdown */}
        {showDropdown && filteredTickers.length > 0 && (
          <div className="absolute z-50 w-full max-w-xs mt-1 bg-gray-800 border border-gray-700 rounded-lg shadow-xl overflow-hidden">
            {filteredTickers.map((t, idx) => (
              <button
                key={t.ticker}
                onClick={() => handleTickerSelect(t.ticker)}
                className={`w-full px-4 py-2.5 text-left flex items-center justify-between hover:bg-gray-700 transition-colors ${
                  highlightedIndex === idx ? 'bg-gray-700' : ''
                } ${recentTickers.includes(t.ticker) ? 'border-l-2 border-blue-500' : ''}`}
              >
                <span className="font-medium text-white">{t.ticker}</span>
                <span className="text-sm text-gray-400 truncate ml-2">{t.name}</span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Quick Action Buttons */}
      <div className="flex flex-wrap justify-center gap-2">
        {QUICK_ACTIONS.map((action) => (
          <button
            key={action.label}
            onClick={() => handleQuickAction(action.query)}
            disabled={!isTickerValid || isLoading}
            className={`group px-4 py-2 text-sm font-medium rounded-full border border-gray-700 transition-all flex items-center gap-2
              ${isTickerValid && !isLoading
                ? 'bg-gray-800/50 hover:bg-gray-700 text-gray-200 hover:text-white hover:border-gray-600 hover:shadow-lg'
                : 'bg-gray-900/50 text-gray-500 cursor-not-allowed border-gray-800'
              }`}
            title={isTickerValid ? action.query.replace('{ticker}', ticker) : 'Select a ticker first'}
          >
            <action.icon className={`w-4 h-4 ${isTickerValid ? 'text-gray-400 group-hover:text-gray-200' : 'text-gray-600'}`} />
            {action.label}
          </button>
        ))}
      </div>

      {/* Helper text */}
      {!isTickerValid && (
        <p className="text-center text-xs text-gray-500">
          Enter a ticker symbol above to enable quick actions
        </p>
      )}
    </div>
  );
}
