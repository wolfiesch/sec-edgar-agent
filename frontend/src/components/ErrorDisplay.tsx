import { AlertTriangle, XCircle } from 'lucide-react';

interface ErrorDisplayProps {
  error: string;
  onDismiss?: () => void;
}

export function ErrorDisplay({ error, onDismiss }: ErrorDisplayProps) {
  return (
    <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 flex items-start gap-3">
      <AlertTriangle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
      <div className="flex-1">
        <h3 className="text-sm font-medium text-red-200">Execution Error</h3>
        <p className="mt-1 text-sm text-red-300/90">{error}</p>
      </div>
      {onDismiss && (
        <button 
            onClick={onDismiss}
            className="text-red-400 hover:text-red-300 transition-colors"
        >
            <XCircle className="w-5 h-5" />
        </button>
      )}
    </div>
  );
}
