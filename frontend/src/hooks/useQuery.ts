import { useState, useCallback } from 'react';
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
    const [events, setEvents] = useState<WorkflowEvent[]>([]);

    const submitQuery = useCallback(async (q: string) => {
        setQuery(q);
        setIsProcessing(true);
        setEvents([]);

        // Generate a simple query ID for history tracking
        const newQueryId = `q_${Date.now()}`;
        setQueryId(newQueryId);

        // Add planning event
        setEvents([{
            phase: 'planning',
            message: 'Analyzing your question...',
            data: null,
            timestamp: new Date().toISOString()
        }]);

        try {
            // Call the Fly.io chat API
            const res = await fetch('/api/v1/chat/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    messages: [{ role: 'user', content: q }],
                    stream: false
                })
            });

            if (!res.ok) {
                const errorData = await res.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Failed to get response');
            }

            const data = await res.json();

            // Add execution event
            setEvents(prev => [...prev, {
                phase: 'executing',
                message: 'Searching SEC filings...',
                data: null,
                timestamp: new Date().toISOString()
            }]);

            // Add completion event with the answer
            setEvents(prev => [...prev, {
                phase: 'complete',
                message: data.answer,
                data: { citations: data.citations, usage: data.usage },
                timestamp: new Date().toISOString()
            }]);

        } catch (e) {
            console.error(e);
            setEvents(prev => [...prev, {
                phase: 'error',
                message: e instanceof Error ? e.message : 'An error occurred',
                data: null,
                timestamp: new Date().toISOString()
            }]);
        } finally {
            setIsProcessing(false);
        }
    }, []);

    const reset = useCallback(() => {
        setQuery('');
        setQueryId(null);
        setIsProcessing(false);
        setEvents([]);
    }, []);

    return {
        query,
        queryId,
        isProcessing,
        events,
        connectionStatus: 'connected', // Always "connected" for REST API
        submitQuery,
        reset
    };
}
