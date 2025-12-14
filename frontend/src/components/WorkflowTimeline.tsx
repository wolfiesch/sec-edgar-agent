import type { WorkflowEvent } from '../types';
import { CheckCircle2, Circle, Loader2, AlertCircle, Wifi, WifiOff } from 'lucide-react';
import { twMerge } from 'tailwind-merge';
import { ToolExecutionCard } from './ToolExecutionCard';

interface WorkflowTimelineProps {
  events: WorkflowEvent[];
  isConnecting?: boolean;
  connectionStatus?: 'disconnected' | 'connecting' | 'connected' | 'error';
}

import { useEffect, useRef } from 'react';

export function WorkflowTimeline({ events, isConnecting, connectionStatus }: WorkflowTimelineProps) {
  // Show connecting state when waiting for first event
  const showConnecting = isConnecting || connectionStatus === 'connecting';
  const showConnectionError = connectionStatus === 'error' && events.length === 0;

  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when events change
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }
  }, [events, showConnecting, showConnectionError]);

  return (
    <div className="space-y-4 h-full flex flex-col">
      <div className="flex items-center justify-between shrink-0">
        <h3 className="text-lg font-semibold text-slate-200">Execution Timeline</h3>
        {connectionStatus && (
          <ConnectionIndicator status={connectionStatus} />
        )}
      </div>
      
      {/* Scrollable Container */}
      <div className="flex-1 overflow-y-auto custom-scrollbar pr-2 -mr-2">
        <div className="relative border-l-2 border-slate-700/50 ml-3 space-y-8 pb-4">
          {/* Connecting skeleton */}
          {showConnecting && events.length === 0 && (
            <div className="relative pl-8 animate-pulse">
              <span className="absolute -left-[9px] top-1 w-5 h-5 rounded-full border-2 bg-slate-900 flex items-center justify-center border-sky-500 text-sky-500 shadow-[0_0_10px_rgba(14,165,233,0.3)]">
                <Loader2 className="w-3 h-3 animate-spin" />
              </span>
              <div className="flex flex-col gap-2">
                <div className="h-4 w-20 bg-slate-700/50 rounded" />
                <div className="h-4 w-48 bg-slate-800/50 rounded" />
              </div>
            </div>
          )}

          {/* Connection error state */}
          {showConnectionError && (
            <div className="relative pl-8">
              <span className="absolute -left-[9px] top-1 w-5 h-5 rounded-full border-2 bg-slate-900 flex items-center justify-center border-red-500 text-red-500">
                <WifiOff className="w-3 h-3" />
              </span>
              <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3">
                <span className="text-sm text-red-400 uppercase tracking-wider font-bold mb-1 block">
                  Connection Failed
                </span>
                <p className="text-slate-400 text-sm">
                  Unable to connect to the server. Please check your internet connection or try again later.
                </p>
              </div>
            </div>
          )}

          {events.map((event, idx) => (
            <div key={idx} className="relative pl-8 animate-in fade-in slide-in-from-bottom-2 duration-300 fill-mode-both" style={{ animationDelay: `${idx * 50}ms` }}>
              <span className={twMerge(
                "absolute -left-[9px] top-1 w-5 h-5 rounded-full border-2 bg-slate-900 flex items-center justify-center shadow-md z-10",
                getPhaseColor(event.phase)
              )}>
                {getPhaseIcon(event.phase)}
              </span>
              
              <div className="group relative">
                {/* Connector line overlay for active feel */}
                <div className="absolute -left-8 top-6 bottom-0 w-0.5 bg-gradient-to-b from-transparent to-transparent group-hover:via-slate-600 transition-all" />

                <div className="flex flex-col">
                  <span className="text-xs text-slate-500 uppercase tracking-wider font-bold mb-1.5 flex items-center gap-2">
                    {event.phase.replace('_', ' ')}
                    <span className="text-[10px] font-normal opacity-50 bg-slate-800 px-1.5 py-0.5 rounded">
                      {new Date(event.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                    </span>
                  </span>
                  
                  {/* Special handling for tool execution results */}
                  {event.phase === 'task_complete' && event.data && event.data.result ? (
                      <div className="mt-1">
                          <p className="text-slate-300 mb-3">{event.message}</p>
                          <ToolExecutionCard 
                            toolName={event.data.result.tool || 'Unknown Tool'}
                            args={event.data.result.arguments || {}}
                            result={event.data.result.output}
                            success={true} 
                            timestamp={event.timestamp}
                          />
                      </div>
                  ) : (
                      <div className="bg-slate-800/30 border border-slate-700/50 rounded-lg p-3 hover:bg-slate-800/50 transition-colors">
                        <p className="text-slate-300 whitespace-pre-wrap text-sm leading-relaxed">
                            {event.phase === 'complete' || event.message.length > 300 
                                ? event.message.slice(0, 300) + (event.message.length > 300 ? "..." : "") 
                                : event.message}
                        </p>
                        
                        {event.data && event.phase !== 'complete' && (
                            <div className="mt-3 text-xs bg-slate-950/50 p-2.5 rounded border border-slate-800 font-mono text-slate-400 overflow-x-auto">
                              <pre>{JSON.stringify(event.data, null, 2)}</pre>
                            </div>
                        )}
                      </div>
                  )}
                </div>
              </div>
            </div>
          ))}

          {/* Invisible element to scroll to */}
          <div ref={scrollRef} />

          {events.length === 0 && !showConnecting && !showConnectionError && (
            <div className="pl-8 text-slate-500 italic py-4">
              Waiting for your instructions...
            </div>
          )}
        </div>
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
