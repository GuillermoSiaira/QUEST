"use client";

import { useQuestFeed } from "@/hooks/useQuestFeed";
import { EpochHeader } from "@/components/EpochHeader";
import { RiskTable } from "@/components/RiskTable";
import { TimelineCharts } from "@/components/TimelineCharts";
import { EpochInterpretation } from "@/components/EpochInterpretation";

function ConnectionDot({ status }: { status: string }) {
  const color =
    status === "connected"
      ? "bg-emerald-400"
      : status === "connecting"
      ? "bg-amber-400 animate-pulse"
      : "bg-red-400";
  const label =
    status === "connected"
      ? "Live"
      : status === "connecting"
      ? "Connecting…"
      : "Disconnected — retrying";

  return (
    <div className="flex items-center gap-1.5 text-xs text-zinc-500">
      <span className={`inline-block h-2 w-2 rounded-full ${color}`} />
      {label}
    </div>
  );
}

export default function Dashboard() {
  const { latest, history, status, lastAlert } = useQuestFeed();

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950 font-sans">
      {/* Topbar */}
      <header className="sticky top-0 z-10 border-b border-zinc-200 dark:border-zinc-800 bg-white/80 dark:bg-zinc-900/80 backdrop-blur-sm px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
            QUEST
          </span>
          <span className="hidden sm:inline text-xs text-zinc-400">
            EVM Solvency Monitor
          </span>
        </div>
        <ConnectionDot status={status} />
      </header>

      <main className="max-w-4xl mx-auto px-4 py-6 flex flex-col gap-5">
        {/* Alert banner */}
        {lastAlert && lastAlert.risk.risk_level !== "HEALTHY" && (
          <div
            className={`rounded-lg px-4 py-3 text-sm font-medium border ${
              lastAlert.risk.risk_level === "CRITICAL"
                ? "bg-red-50 border-red-200 text-red-800"
                : "bg-amber-50 border-amber-200 text-amber-800"
            }`}
          >
            {lastAlert.risk.risk_level === "CRITICAL" ? "CRITICAL" : "GREY ZONE"} —
            Epoch #{lastAlert.epoch} | Score:{" "}
            {lastAlert.risk.grey_zone_score.toFixed(4)} |{" "}
            {lastAlert.slashed_validators} slashed validator
            {lastAlert.slashed_validators !== 1 ? "s" : ""}
          </div>
        )}

        {/* Loading state */}
        {!latest && (
          <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 px-6 py-12 flex flex-col items-center gap-3 text-zinc-400">
            <svg
              className="animate-spin h-6 w-6"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8v8z"
              />
            </svg>
            <p className="text-sm">
              {status === "connecting"
                ? "Connecting to pipeline…"
                : "Waiting for first epoch snapshot…"}
            </p>
          </div>
        )}

        {/* Main content — only when we have data */}
        {latest && (
          <>
            <EpochHeader epoch={latest} />
            <EpochInterpretation epoch={latest} />

            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <RiskTable epoch={latest} />
              <div className="flex flex-col gap-5">
                <TimelineCharts history={history} />
              </div>
            </div>
          </>
        )}
      </main>

      <footer className="text-center py-6 text-xs text-zinc-400">
        QUEST — Macroprudential Oracle for the Ethereum Ecosystem
      </footer>
    </div>
  );
}
