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

/**
 * Map technical error messages to user-friendly versions
 */
function getFriendlyErrorMessage(error: string): string {
    const lowerError = error.toLowerCase();

    // Rate limiting
    if (lowerError.includes('rate limit') || lowerError.includes('429') || lowerError.includes('too many requests')) {
        return 'The SEC API rate limit was reached. Please wait a moment and try again.';
    }

    // Connection issues
    if (lowerError.includes('failed to fetch') || lowerError.includes('network') || lowerError.includes('connection')) {
        return 'Unable to connect to the server. Please check your internet connection and try again.';
    }

    // Timeout
    if (lowerError.includes('timeout') || lowerError.includes('timed out')) {
        return 'The request took too long. Try a simpler question or try again later.';
    }

    // Not found
    if (lowerError.includes('not found') || lowerError.includes('404')) {
        return 'The requested company or filing was not found. Please check the company name or ticker.';
    }

    // Authentication
    if (lowerError.includes('401') || lowerError.includes('403') || lowerError.includes('unauthorized') || lowerError.includes('api key')) {
        return 'Authentication failed. Please refresh the page and try again.';
    }

    // Server errors
    if (lowerError.includes('500') || lowerError.includes('502') || lowerError.includes('503') || lowerError.includes('internal server')) {
        return 'The server encountered an error. Please try again in a few moments.';
    }

    // OpenAI/LLM errors
    if (lowerError.includes('openai') || lowerError.includes('llm') || lowerError.includes('model')) {
        return 'The AI service is temporarily unavailable. Please try again shortly.';
    }

    // Default: return original if short enough, otherwise generic
    if (error.length < 100) {
        return error;
    }
    return 'An unexpected error occurred. Please try again.';
}

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
            const streamUrl = `/api/v1/chat/stream?query=${encodeURIComponent(q)}`;

            // Use fetch with streaming since EventSource doesn't support custom headers.
            // API auth must be added by a trusted server-side proxy, not browser JS.
            const response = await fetch(streamUrl, {
                method: 'GET',
                headers: {
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
                            // Apply friendly error message if this is an error phase
                            const message = eventData.phase === 'error'
                                ? getFriendlyErrorMessage(eventData.message)
                                : eventData.message;

                            const workflowEvent: WorkflowEvent = {
                                phase: eventData.phase as WorkflowPhase,
                                message,
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
            const rawMessage = e instanceof Error ? e.message : 'An error occurred';
            setEvents(prev => [...prev, {
                phase: 'error',
                message: getFriendlyErrorMessage(rawMessage),
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
