"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import type { EpochStatus, FeedMessage } from "@/lib/types";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000/ws/feed";
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const RECONNECT_DELAY_MS = 3000;
const MAX_HISTORY = 50;
const POLL_INTERVAL_SECONDS = Number(
  process.env.NEXT_PUBLIC_POLL_INTERVAL_SECONDS ?? 60
);
const POLL_INTERVAL_MS = Math.max(5, Math.round(POLL_INTERVAL_SECONDS * 1000));

export type ConnectionStatus = "connecting" | "connected" | "disconnected";

interface QuestFeedState {
  latest: EpochStatus | null;
  history: EpochStatus[];
  status: ConnectionStatus;
  lastAlert: EpochStatus | null;
  secondsToRefresh: number | null;
  snapshotAgeSeconds: number | null;
}

export function useQuestFeed(): QuestFeedState {
  const [latest, setLatest] = useState<EpochStatus | null>(null);
  const [history, setHistory] = useState<EpochStatus[]>([]);
  const [connStatus, setConnStatus] = useState<ConnectionStatus>("connecting");
  const [lastAlert, setLastAlert] = useState<EpochStatus | null>(null);
  const [secondsToRefresh, setSecondsToRefresh] = useState<number | null>(null);
  const [snapshotAgeSeconds, setSnapshotAgeSeconds] = useState<number | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pollTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const countdownTimer = useRef<ReturnType<typeof setInterval> | null>(null);
  const isMounted = useRef(true);
  const lastMessageAtRef = useRef<number | null>(null);
  const nextRefreshAtRef = useRef<number | null>(null);
  const lastSnapshotAtRef = useRef<number | null>(null);

  const markRefresh = useCallback(() => {
    nextRefreshAtRef.current = Date.now() + POLL_INTERVAL_MS;
  }, []);

  const pushSnapshot = useCallback(
    (snapshot: EpochStatus, messageType?: string) => {
      setLatest(snapshot);
      setHistory((prev) => {
        const last = prev[prev.length - 1];
        if (
          last &&
          last.epoch === snapshot.epoch &&
          last.timestamp === snapshot.timestamp
        ) {
          return prev;
        }
        const next = [...prev, snapshot];
        return next.length > MAX_HISTORY ? next.slice(-MAX_HISTORY) : next;
      });

      if (messageType === "alert") {
        setLastAlert(snapshot);
      }

      lastMessageAtRef.current = Date.now();
      lastSnapshotAtRef.current = lastMessageAtRef.current;
      markRefresh();
    },
    [markRefresh]
  );

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
          pushSnapshot(msg.data, msg.type);
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
  }, [pushSnapshot]);

  // Carga el historial acumulado por el backend al montar
  useEffect(() => {
    fetch(`${API_URL}/api/history?n=${MAX_HISTORY}`)
      .then((r) => r.json())
      .then((data: EpochStatus[]) => {
        if (!isMounted.current || !Array.isArray(data) || data.length === 0) return;
        setHistory(data);
        setLatest(data[data.length - 1]);
        lastMessageAtRef.current = Date.now();
        lastSnapshotAtRef.current = lastMessageAtRef.current;
        markRefresh();
      })
      .catch(() => {
        // Backend todavia no tiene datos — el WebSocket los va a proveer
      });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const tick = () => {
      if (nextRefreshAtRef.current === null) {
        setSecondsToRefresh(null);
      } else {
        const remainingMs = Math.max(0, nextRefreshAtRef.current - Date.now());
        setSecondsToRefresh(Math.ceil(remainingMs / 1000));
      }

      if (lastSnapshotAtRef.current === null) {
        setSnapshotAgeSeconds(null);
        return;
      }

      const ageMs = Math.max(0, Date.now() - lastSnapshotAtRef.current);
      setSnapshotAgeSeconds(Math.floor(ageMs / 1000));
    };

    markRefresh();
    tick();
    countdownTimer.current = setInterval(tick, 1000);

    return () => {
      if (countdownTimer.current) clearInterval(countdownTimer.current);
      countdownTimer.current = null;
    };
  }, [markRefresh]);

  const pollStatus = useCallback(async () => {
    if (!isMounted.current) return false;
    const now = Date.now();
    const lastMessageAt = lastMessageAtRef.current;
    const shouldPoll = !lastMessageAt || now - lastMessageAt > POLL_INTERVAL_MS;
    if (!shouldPoll) return false;

    try {
      const res = await fetch(`${API_URL}/api/status`);
      if (!res.ok) return true;
      const data = (await res.json()) as EpochStatus;
      if (data && typeof data.epoch === "number") {
        pushSnapshot(data, "snapshot");
      }
      return true;
    } catch {
      // ignore polling failures
      return true;
    }
  }, [pushSnapshot]);

  useEffect(() => {
    let cancelled = false;
    const loop = async () => {
      if (cancelled) return;
      const didPoll = await pollStatus();
      if (cancelled) return;
      if (didPoll) {
        markRefresh();
      }
      pollTimer.current = setTimeout(loop, POLL_INTERVAL_MS);
    };

    loop();

    return () => {
      cancelled = true;
      if (pollTimer.current) clearTimeout(pollTimer.current);
      pollTimer.current = null;
    };
  }, [pollStatus, markRefresh]);

  useEffect(() => {
    isMounted.current = true;
    connect();

    return () => {
      isMounted.current = false;
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return {
    latest,
    history,
    status: connStatus,
    lastAlert,
    secondsToRefresh,
    snapshotAgeSeconds,
  };
}
