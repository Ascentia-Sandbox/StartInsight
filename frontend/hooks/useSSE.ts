'use client';

import { useState, useEffect, useCallback, useRef } from 'react';

interface UseSSEOptions<T> {
  url: string;
  enabled?: boolean;
  onMessage?: (data: T) => void;
  onError?: (error: Event) => void;
  fallbackInterval?: number; // ms, for polling fallback
  fallbackFetcher?: () => Promise<T>;
}

interface UseSSEResult<T> {
  data: T | null;
  isLive: boolean;
  isConnecting: boolean;
  error: Event | null;
  lastUpdate: Date | null;
}

export function useSSE<T>({
  url,
  enabled = true,
  onMessage,
  onError,
  fallbackInterval = 30000,
  fallbackFetcher,
}: UseSSEOptions<T>): UseSSEResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [isLive, setIsLive] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<Event | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const fallbackTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const cleanup = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    if (fallbackTimerRef.current) {
      clearInterval(fallbackTimerRef.current);
      fallbackTimerRef.current = null;
    }
  }, []);

  const startFallbackPolling = useCallback(() => {
    if (!fallbackFetcher || fallbackTimerRef.current) return;

    fallbackTimerRef.current = setInterval(async () => {
      try {
        const result = await fallbackFetcher();
        setData(result);
        setLastUpdate(new Date());
        onMessage?.(result);
      } catch {
        // Silently continue polling
      }
    }, fallbackInterval);
  }, [fallbackFetcher, fallbackInterval, onMessage]);

  useEffect(() => {
    if (!enabled) {
      cleanup();
      return;
    }

    setIsConnecting(true);

    try {
      const eventSource = new EventSource(url);
      eventSourceRef.current = eventSource;

      eventSource.onopen = () => {
        setIsLive(true);
        setIsConnecting(false);
        setError(null);

        // Stop fallback polling if SSE connects
        if (fallbackTimerRef.current) {
          clearInterval(fallbackTimerRef.current);
          fallbackTimerRef.current = null;
        }
      };

      eventSource.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data) as T;
          setData(parsed);
          setLastUpdate(new Date());
          onMessage?.(parsed);
        } catch {
          // Ignore parse errors
        }
      };

      eventSource.onerror = (err) => {
        setIsLive(false);
        setIsConnecting(false);
        setError(err);
        onError?.(err);

        // Close failed SSE and fallback to polling
        eventSource.close();
        eventSourceRef.current = null;
        startFallbackPolling();
      };
    } catch {
      setIsConnecting(false);
      // SSE not supported, use polling
      startFallbackPolling();
    }

    return cleanup;
  }, [url, enabled]);

  return { data, isLive, isConnecting, error, lastUpdate };
}
