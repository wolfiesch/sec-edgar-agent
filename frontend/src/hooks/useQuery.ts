import { useState, useCallback, useEffect, useRef } from 'react';
import { useWebSocket } from './useWebSocket';
import type { WorkflowEvent } from '../types';

interface UseQueryResult {
    query: string;
    queryId: string | null;
    isProcessing: boolean;
    events: WorkflowEvent[];
    connectionStatus: string;
    submitQuery: (q: string) => Promise<void>;
    reset: () => void;
}

export function useQuery(): UseQueryResult {
    const [query, setQuery] = useState('');
    const [queryId, setQueryId] = useState<string | null>(null);
    const [isProcessing, setIsProcessing] = useState(false);
    const sentQueryRef = useRef(false);

    const { events, status: connectionStatus, sendMessage } = useWebSocket(queryId);

    const submitQuery = useCallback(async (q: string) => {
        setQuery(q);
        setIsProcessing(true);
        sentQueryRef.current = false;

        try {
            const res = await fetch('http://localhost:8000/api/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: q })
            });

            if (!res.ok) throw new Error('Failed to start query');

            const data = await res.json();
            setQueryId(data.query_id);
        } catch (e) {
            console.error(e);
            setIsProcessing(false);
            alert('Failed to start query');
        }
    }, []);

    // Send query over WebSocket once connected
    useEffect(() => {
        if (connectionStatus === 'connected' && query && queryId && !sentQueryRef.current) {
            sendMessage(query);
            sentQueryRef.current = true;
        }
    }, [connectionStatus, query, queryId, sendMessage]);

    // Stop processing when complete or error
    useEffect(() => {
        const lastEvent = events[events.length - 1];
        if (lastEvent && (lastEvent.phase === 'complete' || lastEvent.phase === 'error')) {
            setIsProcessing(false);
        }
    }, [events]);

    const reset = useCallback(() => {
        setQuery('');
        setQueryId(null);
        setIsProcessing(false);
        sentQueryRef.current = false;
    }, []);

    return {
        query,
        queryId,
        isProcessing,
        events,
        connectionStatus,
        submitQuery,
        reset
    };
}
