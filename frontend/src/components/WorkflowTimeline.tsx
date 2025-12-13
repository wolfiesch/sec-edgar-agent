import type { WorkflowEvent } from '../types';
import { CheckCircle2, Circle, Loader2, AlertCircle } from 'lucide-react';
import { twMerge } from 'tailwind-merge';
import { ToolExecutionCard } from './ToolExecutionCard';

interface WorkflowTimelineProps {
  events: WorkflowEvent[];
}

export function WorkflowTimeline({ events }: WorkflowTimelineProps) {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-200">Execution Timeline</h3>
      <div className="relative border-l-2 border-gray-700 ml-3 space-y-6 pb-4">
        {events.map((event, idx) => (
          <div key={idx} className="relative pl-8">
            <span className={twMerge(
              "absolute -left-[9px] top-1 w-5 h-5 rounded-full border-2 bg-gray-900 flex items-center justify-center",
              getPhaseColor(event.phase)
            )}>
              {getPhaseIcon(event.phase)}
            </span>
            <div className="flex flex-col">
              <span className="text-sm text-gray-400 uppercase tracking-wider font-bold mb-1">
                {event.phase.replace('_', ' ')}
              </span>
              
              {/* Special handling for tool execution results */}
              {event.phase === 'task_complete' && event.data && event.data.result ? (
                  <div className="mt-1">
                      <p className="text-gray-200 mb-2">{event.message}</p>
                      <ToolExecutionCard 
                        toolName={event.data.result.tool || 'Unknown Tool'}
                        args={event.data.result.arguments || {}}
                        result={event.data.result.output}
                        success={true} // Task complete implies success usually, or check event.data.result.error
                        timestamp={event.timestamp}
                      />
                  </div>
              ) : (
                  <>
                    <p className="text-gray-200 whitespace-pre-wrap">
                        {event.phase === 'complete' || event.message.length > 300 
                            ? event.message.slice(0, 300) + (event.message.length > 300 ? "..." : "") 
                            : event.message}
                    </p>
                    
                    {event.data && event.phase !== 'complete' && (
                        <div className="mt-2 text-xs bg-gray-800 p-2 rounded overflow-x-auto border border-gray-700 font-mono text-gray-300">
                        <pre>{JSON.stringify(event.data, null, 2)}</pre>
                        </div>
                    )}
                  </>
              )}

              <span className="text-xs text-gray-500 mt-1">
                {new Date(event.timestamp).toLocaleTimeString()}
              </span>
            </div>
          </div>
        ))}
        {events.length === 0 && (
          <div className="pl-8 text-gray-500 italic">No events yet...</div>
        )}
      </div>
    </div>
  );
}

function getPhaseColor(phase: string) {
  switch (phase) {
    case 'error': return 'border-red-500 text-red-500';
    case 'complete': return 'border-green-500 text-green-500';
    case 'planning': return 'border-blue-500 text-blue-500';
    case 'planned': return 'border-blue-400 text-blue-400';
    case 'executing': return 'border-purple-500 text-purple-500';
    case 'tool_start': return 'border-orange-500 text-orange-500';
    case 'task_complete': return 'border-emerald-500 text-emerald-500';
    case 'validating': return 'border-yellow-500 text-yellow-500';
    case 'validated': return 'border-green-400 text-green-400';
    case 'validation_failed': return 'border-red-400 text-red-400';
    case 'retrying': return 'border-amber-500 text-amber-500';
    case 'warning': return 'border-yellow-400 text-yellow-400';
    case 'synthesizing': return 'border-indigo-500 text-indigo-500';
    default: return 'border-gray-500 text-gray-500';
  }
}

function getPhaseIcon(phase: string) {
  switch (phase) {
    case 'error': return <AlertCircle className="w-3 h-3" />;
    case 'validation_failed': return <AlertCircle className="w-3 h-3" />;
    case 'warning': return <AlertCircle className="w-3 h-3" />;
    case 'complete': return <CheckCircle2 className="w-3 h-3" />;
    case 'task_complete': return <CheckCircle2 className="w-3 h-3" />;
    case 'validated': return <CheckCircle2 className="w-3 h-3" />;
    case 'planned': return <CheckCircle2 className="w-3 h-3" />;
    case 'executing': return <Loader2 className="w-3 h-3 animate-spin" />;
    case 'tool_start': return <Loader2 className="w-3 h-3 animate-spin" />;
    case 'validating': return <Loader2 className="w-3 h-3 animate-spin" />;
    case 'synthesizing': return <Loader2 className="w-3 h-3 animate-spin" />;
    case 'retrying': return <Loader2 className="w-3 h-3 animate-spin" />;
    default: return <Circle className="w-3 h-3" />;
  }
}
