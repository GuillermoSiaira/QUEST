"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import type { EpochStatus, FeedMessage } from "@/lib/types";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000/ws/feed";
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const RECONNECT_DELAY_MS = 3000;
const MAX_HISTORY = 50;

export type ConnectionStatus = "connecting" | "connected" | "disconnected";

interface QuestFeedState {
  latest: EpochStatus | null;
  history: EpochStatus[];
  status: ConnectionStatus;
  lastAlert: EpochStatus | null;
}

export function useQuestFeed(): QuestFeedState {
  const [latest, setLatest] = useState<EpochStatus | null>(null);
  const [history, setHistory] = useState<EpochStatus[]>([]);
  const [connStatus, setConnStatus] = useState<ConnectionStatus>("connecting");
  const [lastAlert, setLastAlert] = useState<EpochStatus | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isMounted = useRef(true);

  const connect = useCallback(() => {
    if (!isMounted.current) return;

    setConnStatus("connecting");
    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      if (!isMounted.current) return;
      setConnStatus("connected");
    };

    ws.onmessage = (event: MessageEvent) => {
      if (!isMounted.current) return;
      try {
        const msg: FeedMessage = JSON.parse(event.data as string);

        if (msg.type === "ping") return;

        if (msg.data) {
          const snapshot = msg.data;
          setLatest(snapshot);
          setHistory((prev) => {
            const next = [...prev, snapshot];
            return next.length > MAX_HISTORY ? next.slice(-MAX_HISTORY) : next;
          });

          if (msg.type === "alert") {
            setLastAlert(snapshot);
          }
        }
      } catch {
        // malformed message — ignore
      }
    };

    ws.onclose = () => {
      if (!isMounted.current) return;
      setConnStatus("disconnected");
      reconnectTimer.current = setTimeout(connect, RECONNECT_DELAY_MS);
    };

    ws.onerror = () => {
      ws.close();
    };
  }, []);

  // Carga el historial acumulado por el backend al montar
  useEffect(() => {
    fetch(`${API_URL}/api/history?n=${MAX_HISTORY}`)
      .then((r) => r.json())
      .then((data: EpochStatus[]) => {
        if (!isMounted.current || !Array.isArray(data) || data.length === 0) return;
        setHistory(data);
        setLatest(data[data.length - 1]);
      })
      .catch(() => {
        // Backend todavia no tiene datos — el WebSocket los va a proveer
      });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    isMounted.current = true;
    connect();

    return () => {
      isMounted.current = false;
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return { latest, history, status: connStatus, lastAlert };
}
