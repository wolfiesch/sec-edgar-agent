import { useEffect, useRef, useState, useCallback } from 'react';
import type { WorkflowEvent } from '../types';

export function useWebSocket(queryId: string | null) {
  const [events, setEvents] = useState<WorkflowEvent[]>([]);
  const [status, setStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected');
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!queryId) return;

    // Reset state for new query
    setEvents([]);
    setStatus('connecting');

    const wsUrl = `ws://localhost:8000/api/query/${queryId}/stream`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('WS Connected');
      setStatus('connected');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        // Add timestamp if missing
        const eventData = { ...data, timestamp: new Date().toISOString() };
        setEvents(prev => [...prev, eventData]);
      } catch (e) {
        console.error('Failed to parse WS message', e);
      }
    };

    ws.onerror = (e) => {
      console.error('WS Error', e);
      setStatus('error');
    };

    ws.onclose = () => {
      console.log('WS Closed');
      if (status !== 'error') {
          setStatus('disconnected');
      }
    };

    return () => {
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close();
      }
    };
  }, [queryId]);

  const sendMessage = useCallback((msg: string) => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(msg);
      }
  }, []);

  return { events, status, sendMessage };
}
