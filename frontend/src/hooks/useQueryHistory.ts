import { useState, useEffect, useCallback } from 'react';

const HISTORY_KEY = 'sec_agent_history';

export interface HistoryItem {
  query: string;
  timestamp: string;
  queryId: string;
}

export function useQueryHistory() {
  const [history, setHistory] = useState<HistoryItem[]>([]);

  useEffect(() => {
    const stored = localStorage.getItem(HISTORY_KEY);
    if (stored) {
      try {
        setHistory(JSON.parse(stored));
      } catch (e) {
        console.error('Failed to parse history', e);
      }
    }
  }, []);

  const addToHistory = useCallback((query: string, queryId: string) => {
    setHistory(prev => {
      const newItem = { query, queryId, timestamp: new Date().toISOString() };
      // Filter out duplicates (simple query match)? Or keep all?
      // Let's filter duplicates to keep it clean, move to top
      const filtered = prev.filter(item => item.query !== query);
      const newHistory = [newItem, ...filtered].slice(0, 50); // Keep max 50
      localStorage.setItem(HISTORY_KEY, JSON.stringify(newHistory));
      return newHistory;
    });
  }, []);

  const clearHistory = useCallback(() => {
      setHistory([]);
      localStorage.removeItem(HISTORY_KEY);
  }, []);

  return { history, addToHistory, clearHistory };
}
