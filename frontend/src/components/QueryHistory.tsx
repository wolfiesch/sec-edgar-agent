import { History, Trash2, Clock } from 'lucide-react';

interface HistoryItem {
  query: string;
  timestamp: string;
  queryId: string;
}

interface QueryHistoryProps {
  history: HistoryItem[];
  onSelect: (query: string) => void;
  onClear: () => void;
}

export function QueryHistory({ history, onSelect, onClear }: QueryHistoryProps) {
  if (history.length === 0) return null;

  return (
    <div className="bg-gray-900/50 rounded-xl border border-gray-800 p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider flex items-center gap-2">
            <History className="w-4 h-4" />
            Recent Queries
        </h3>
        <button 
            onClick={onClear}
            className="text-gray-500 hover:text-red-400 transition-colors p-1"
            title="Clear History"
        >
            <Trash2 className="w-4 h-4" />
        </button>
      </div>
      
      <div className="space-y-2 max-h-[300px] overflow-y-auto custom-scrollbar">
        {history.map((item) => (
          <button
            key={item.queryId} // ideally unique
            onClick={() => onSelect(item.query)}
            className="w-full text-left p-2 rounded hover:bg-gray-800/50 transition-colors group"
          >
            <div className="text-gray-300 font-medium truncate group-hover:text-blue-400 transition-colors">
                {item.query}
            </div>
            <div className="text-xs text-gray-600 flex items-center gap-1 mt-1">
                <Clock className="w-3 h-3" />
                {new Date(item.timestamp).toLocaleDateString()} {new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
