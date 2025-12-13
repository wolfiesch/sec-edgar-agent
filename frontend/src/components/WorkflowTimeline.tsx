import type { WorkflowEvent } from '../types';
import { CheckCircle2, Circle, Loader2, AlertCircle, Wifi, WifiOff } from 'lucide-react';
import { twMerge } from 'tailwind-merge';
import { ToolExecutionCard } from './ToolExecutionCard';

interface WorkflowTimelineProps {
  events: WorkflowEvent[];
  isConnecting?: boolean;
  connectionStatus?: 'disconnected' | 'connecting' | 'connected' | 'error';
}

export function WorkflowTimeline({ events, isConnecting, connectionStatus }: WorkflowTimelineProps) {
  // Show connecting state when waiting for first event
  const showConnecting = isConnecting || connectionStatus === 'connecting';
  const showConnectionError = connectionStatus === 'error' && events.length === 0;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-200">Execution Timeline</h3>
        {connectionStatus && (
          <ConnectionIndicator status={connectionStatus} />
        )}
      </div>
      <div className="relative border-l-2 border-gray-700 ml-3 space-y-6 pb-4">
        {/* Connecting skeleton */}
        {showConnecting && events.length === 0 && (
          <div className="relative pl-8 animate-pulse">
            <span className="absolute -left-[9px] top-1 w-5 h-5 rounded-full border-2 bg-gray-900 flex items-center justify-center border-blue-500 text-blue-500">
              <Loader2 className="w-3 h-3 animate-spin" />
            </span>
            <div className="flex flex-col gap-2">
              <div className="h-4 w-20 bg-gray-700 rounded" />
              <div className="h-4 w-48 bg-gray-800 rounded" />
            </div>
          </div>
        )}

        {/* Connection error state */}
        {showConnectionError && (
          <div className="relative pl-8">
            <span className="absolute -left-[9px] top-1 w-5 h-5 rounded-full border-2 bg-gray-900 flex items-center justify-center border-red-500 text-red-500">
              <WifiOff className="w-3 h-3" />
            </span>
            <div className="flex flex-col">
              <span className="text-sm text-red-400 uppercase tracking-wider font-bold mb-1">
                Connection Failed
              </span>
              <p className="text-gray-400 text-sm">
                Unable to connect to the server. Please try again.
              </p>
            </div>
          </div>
        )}

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
        {events.length === 0 && !showConnecting && !showConnectionError && (
          <div className="pl-8 text-gray-500 italic">
            Submit a question to see the agent's execution timeline.
          </div>
        )}
      </div>
    </div>
  );
}

function ConnectionIndicator({ status }: { status: string }) {
  switch (status) {
    case 'connecting':
      return (
        <div className="flex items-center gap-1.5 text-xs text-blue-400">
          <Loader2 className="w-3 h-3 animate-spin" />
          <span>Connecting...</span>
        </div>
      );
    case 'connected':
      return (
        <div className="flex items-center gap-1.5 text-xs text-green-400">
          <Wifi className="w-3 h-3" />
          <span>Live</span>
        </div>
      );
    case 'error':
      return (
        <div className="flex items-center gap-1.5 text-xs text-red-400">
          <WifiOff className="w-3 h-3" />
          <span>Error</span>
        </div>
      );
    default:
      return null;
  }
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
