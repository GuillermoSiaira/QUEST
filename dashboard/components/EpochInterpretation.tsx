"use client";

import { useEffect, useRef, useState } from "react";
import type { EpochStatus } from "@/lib/types";

interface Props {
  epoch: EpochStatus;
  secondsToRefresh?: number | null;
}

export function EpochInterpretation({ epoch, secondsToRefresh }: Props) {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [timestamp, setTimestamp] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const lastEpochRef = useRef<number | null>(null);
  const hasTimestampRef = useRef(false);

  useEffect(() => {
    // Only re-fetch when epoch number changes
    if (epoch.epoch === lastEpochRef.current) return;
    lastEpochRef.current = epoch.epoch;

    // Cancel any in-flight request
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setText("");
    setLoading(true);
    setTimestamp(null);
    hasTimestampRef.current = false;

    (async () => {
      try {
        const res = await fetch("/api/interpret", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(epoch),
          signal: controller.signal,
        });

        if (res.status === 400) return; // StrictMode double-invocation — ignorar
        if (!res.ok || !res.body) {
          setText("Could not generate interpretation.");
          return;
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let accumulated = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          accumulated += decoder.decode(value, { stream: true });
          if (!hasTimestampRef.current) {
            hasTimestampRef.current = true;
            setTimestamp(
              new Date().toLocaleString(undefined, {
                year: "numeric",
                month: "2-digit",
                day: "2-digit",
                hour: "2-digit",
                minute: "2-digit",
              })
            );
          }
          setText(accumulated);
        }
      } catch (err: unknown) {
        if (err instanceof Error && err.name !== "AbortError") {
          setText("Interpretation unavailable.");
        }
      } finally {
        setLoading(false);
      }
    })();

    return () => {
      controller.abort();
      lastEpochRef.current = null; // reset para que StrictMode no bloquee la segunda pasada
    };
  }, [epoch]);

  const formattedCountdown = (() => {
    if (secondsToRefresh === null || secondsToRefresh === undefined) return null;
    const minutes = Math.floor(secondsToRefresh / 60);
    const seconds = secondsToRefresh % 60;
    return `${minutes}:${seconds.toString().padStart(2, "0")}`;
  })();

  const borderColor =
    epoch.risk.risk_level === "CRITICAL"
      ? "border-red-300 dark:border-red-800"
      : epoch.risk.risk_level === "GREY_ZONE"
      ? "border-amber-300 dark:border-amber-800"
      : "border-zinc-200 dark:border-zinc-800";

  return (
    <div
      className={`rounded-xl border ${borderColor} bg-white dark:bg-zinc-900 shadow-sm px-5 py-4`}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-zinc-500 dark:text-zinc-400 uppercase tracking-wide">
            QUEST Analysis
          </span>
          {loading && (
            <span className="inline-block h-1.5 w-1.5 rounded-full bg-indigo-400 animate-pulse" />
          )}
        </div>
        <div className="flex items-center gap-3 text-xs text-zinc-500 dark:text-zinc-400">
          {timestamp && <span>{timestamp}</span>}
          {formattedCountdown && (
            <span>
              Next update in {formattedCountdown}
            </span>
          )}
        </div>
      </div>
      <p className="text-sm leading-relaxed text-zinc-700 dark:text-zinc-300 min-h-[2.5rem]"
         dangerouslySetInnerHTML={{
           __html: (text || (loading ? "\u00A0" : "Waiting for epoch data…"))
             .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
             .replace(/\*(.+?)\*/g, "<em>$1</em>")
         }}
      />
    </div>
  );
}
