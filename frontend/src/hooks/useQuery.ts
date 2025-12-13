import { useState, useCallback, useRef } from 'react';
import type { WorkflowEvent, WorkflowPhase } from '../types';

interface UseQueryResult {
    query: string;
    queryId: string | null;
    isProcessing: boolean;
    events: WorkflowEvent[];
    connectionStatus: string;
    submitQuery: (q: string) => Promise<void>;
    reset: () => void;
}

const API_KEY = 'sec-api-demo';

export function useQuery(): UseQueryResult {
    const [query, setQuery] = useState('');
    const [queryId, setQueryId] = useState<string | null>(null);
    const [isProcessing, setIsProcessing] = useState(false);
    const [events, setEvents] = useState<WorkflowEvent[]>([]);
    const [connectionStatus, setConnectionStatus] = useState('disconnected');
    const eventSourceRef = useRef<EventSource | null>(null);

    const submitQuery = useCallback(async (q: string) => {
        setQuery(q);
        setIsProcessing(true);
        setEvents([]);
        setConnectionStatus('connecting');

        // Generate a simple query ID for history tracking
        const newQueryId = `q_${Date.now()}`;
        setQueryId(newQueryId);

        // Close any existing connection
        if (eventSourceRef.current) {
            eventSourceRef.current.close();
            eventSourceRef.current = null;
        }

        try {
            // Use SSE streaming endpoint
            // Note: EventSource doesn't support custom headers, so we pass API key as query param
            // The backend should support this, or we use fetch with streaming
            const streamUrl = `/api/v1/chat/stream?query=${encodeURIComponent(q)}`;

            // Use fetch with streaming since EventSource doesn't support custom headers
            const response = await fetch(streamUrl, {
                method: 'GET',
                headers: {
                    'X-API-Key': API_KEY,
                    'Accept': 'text/event-stream',
                },
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP ${response.status}: Failed to connect to stream`);
            }

            setConnectionStatus('connected');

            const reader = response.body?.getReader();
            if (!reader) {
                throw new Error('Response body is not readable');
            }

            const decoder = new TextDecoder();
            let buffer = '';

            // Read the stream
            while (true) {
                const { done, value } = await reader.read();

                if (done) {
                    setConnectionStatus('disconnected');
                    break;
                }

                // Decode the chunk and add to buffer
                buffer += decoder.decode(value, { stream: true });

                // Process complete SSE events (separated by double newlines)
                const lines = buffer.split('\n\n');
                buffer = lines.pop() || ''; // Keep incomplete line in buffer

                for (const eventText of lines) {
                    if (!eventText.trim()) continue;

                    // Parse SSE data line
                    const dataMatch = eventText.match(/^data:\s*(.+)$/m);
                    if (dataMatch) {
                        try {
                            const eventData = JSON.parse(dataMatch[1]);

                            // Create workflow event from SSE data
                            const workflowEvent: WorkflowEvent = {
                                phase: eventData.phase as WorkflowPhase,
                                message: eventData.message,
                                data: eventData.data,
                                timestamp: new Date().toISOString(),
                            };

                            // Add event to timeline
                            setEvents(prev => [...prev, workflowEvent]);

                            // Check for terminal states
                            if (eventData.phase === 'complete' || eventData.phase === 'error') {
                                setIsProcessing(false);
                            }
                        } catch (parseError) {
                            console.error('Failed to parse SSE event:', parseError, eventText);
                        }
                    }
                }
            }

        } catch (e) {
            console.error('SSE connection error:', e);
            setConnectionStatus('error');
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
        // Close any existing connection
        if (eventSourceRef.current) {
            eventSourceRef.current.close();
            eventSourceRef.current = null;
        }
        setQuery('');
        setQueryId(null);
        setIsProcessing(false);
        setEvents([]);
        setConnectionStatus('disconnected');
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
