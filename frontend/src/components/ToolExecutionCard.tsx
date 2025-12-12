import { ChevronDown, ChevronRight, Terminal, CheckCircle2, XCircle } from 'lucide-react';
import { useState } from 'react';
import clsx from 'clsx';

interface ToolExecutionCardProps {
  toolName: string;
  args: Record<string, any>;
  result: any;
  success: boolean;
  timestamp?: string;
}

export function ToolExecutionCard({ toolName, args, result, success, timestamp }: ToolExecutionCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  // Parse result if it's a stringified JSON (common in tool outputs)
  let displayResult = result;
  if (typeof result === 'string') {
      try {
          // If result is huge, maybe truncate?
          if (result.length > 500 && !isExpanded) {
              displayResult = result.slice(0, 500) + '...';
          }
      } catch (e) {
          // keep as string
      }
  }

  return (
    <div className="bg-gray-900/40 rounded-lg border border-gray-800 overflow-hidden">
      <div 
        className="flex items-center gap-3 p-3 cursor-pointer hover:bg-gray-800/50 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className={clsx("p-1.5 rounded-md", success ? "bg-green-500/10 text-green-400" : "bg-red-500/10 text-red-400")}>
            <Terminal className="w-4 h-4" />
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-medium text-gray-200 text-sm truncate">{toolName}</span>
            <span className="text-xs text-gray-500">{timestamp && new Date(timestamp).toLocaleTimeString()}</span>
          </div>
          <div className="text-xs text-gray-500 truncate font-mono mt-0.5">
            {JSON.stringify(args)}
          </div>
        </div>

        {success ? (
             <CheckCircle2 className="w-4 h-4 text-green-500/50" />
        ) : (
             <XCircle className="w-4 h-4 text-red-500/50" />
        )}
        
        {isExpanded ? <ChevronDown className="w-4 h-4 text-gray-500" /> : <ChevronRight className="w-4 h-4 text-gray-500" />}
      </div>

      {isExpanded && (
        <div className="px-3 pb-3 pt-0 border-t border-gray-800/50">
            <div className="mt-3 space-y-2">
                <div>
                    <span className="text-xs uppercase tracking-wider text-gray-500 font-semibold">Input</span>
                    <pre className="mt-1 text-xs bg-black/30 p-2 rounded text-gray-300 overflow-x-auto">
                        {JSON.stringify(args, null, 2)}
                    </pre>
                </div>
                <div>
                    <span className="text-xs uppercase tracking-wider text-gray-500 font-semibold">Output</span>
                    <pre className="mt-1 text-xs bg-black/30 p-2 rounded text-gray-300 overflow-x-auto whitespace-pre-wrap">
{typeof displayResult === 'object' ? JSON.stringify(displayResult, null, 2) : String(displayResult)}
                    </pre>
                </div>
            </div>
        </div>
      )}
    </div>
  );
}
