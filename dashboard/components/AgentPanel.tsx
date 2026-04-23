"use client";

import { useMemo } from "react";

interface AgentState {
  exposureRatio: number;  // 0–1
  betaGZS: number;        // 0–1
  utility: number;        // signed, scaled
  gzs: number;            // current GZS
  lambda: number;         // risk aversion
}

interface Props {
  gzs?: number;
  /** If true, uses simulated data instead of contract read */
  preview?: boolean;
}

function ExposureGauge({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color =
    pct > 70
      ? "bg-emerald-500"
      : pct > 40
      ? "bg-amber-400"
      : "bg-red-500";

  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex justify-between items-baseline">
        <span className="text-[10px] text-zinc-400 uppercase tracking-widest font-medium">
          Exposure Ratio
        </span>
        <span className="text-sm font-mono font-bold text-zinc-900 dark:text-zinc-100">
          {pct}%
        </span>
      </div>
      <div className="h-2 w-full rounded-full bg-zinc-100 dark:bg-zinc-800 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

function StatRow({
  label,
  value,
  sub,
  highlight,
}: {
  label: string;
  value: string;
  sub?: string;
  highlight?: boolean;
}) {
  return (
    <div className="flex items-center justify-between py-2.5 border-b border-zinc-50 dark:border-zinc-800/50 last:border-0">
      <div className="flex flex-col">
        <span className="text-sm text-zinc-500 dark:text-zinc-400">{label}</span>
        {sub && <span className="text-[10px] text-zinc-400 dark:text-zinc-600">{sub}</span>}
      </div>
      <span
        className={`text-sm font-mono font-medium ${
          highlight
            ? "text-red-600 dark:text-red-400"
            : "text-zinc-900 dark:text-zinc-100"
        }`}
      >
        {value}
      </span>
    </div>
  );
}

function computeAgentState(gzs: number, lambda: number): AgentState {
  const sigmaBase = 0.05;
  const k = Math.log(10); // ≈ 2.302585 — calibrated for exp form
  // calibrated so: exposure(GZS=0)=90%, exposure(GZS=1.0)=0%
  // under exp form, exposure(GZS=0.5)≈68% (convexity near the threshold)
  const expectedReturn = 10 * (lambda / 2) * sigmaBase * sigmaBase;

  const sigmaSquared = sigmaBase * sigmaBase * Math.exp(k * gzs);
  const riskTerm = (lambda / 2) * sigmaSquared;
  const utility = expectedReturn - riskTerm;

  const exposureRatio = expectedReturn === 0
    ? 0
    : Math.max(0, Math.min(1, utility / expectedReturn));

  const maxBeta = 1.0;
  const betaGZS = exposureRatio * maxBeta;

  return { exposureRatio, betaGZS, utility, gzs, lambda };
}

export function AgentPanel({ gzs = 0.12, preview = false }: Props) {
  const lambda = 0.6;
  const agent = useMemo(() => computeAgentState(gzs, lambda), [gzs]);

  const utilityDisplay = agent.utility >= 0
    ? `+${(agent.utility * 1e6).toFixed(3)} × 10⁻⁶`
    : `${(agent.utility * 1e6).toFixed(3)} × 10⁻⁶`;

  const utilityPositive = agent.utility >= 0;

  return (
    <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-sm overflow-hidden">
      <div className="px-6 py-3 border-b border-zinc-100 dark:border-zinc-800 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-zinc-700 dark:text-zinc-300 uppercase tracking-wide">
          QUEST Agent — Mean-Variance State
        </h3>
        {preview && (
          <span className="text-[10px] text-zinc-400 border border-zinc-200 dark:border-zinc-700 rounded px-1.5 py-0.5">
            preview
          </span>
        )}
      </div>

      <div className="px-6 pt-5 pb-3">
        <ExposureGauge value={agent.exposureRatio} />
      </div>

      <div className="px-6 pb-4">
        <StatRow
          label="Utility  U"
          sub="E(R) − (λ/2)·σ²·exp(k·GZS)"
          value={utilityDisplay}
          highlight={!utilityPositive}
        />
        <StatRow
          label="Beta GZS"
          sub="exposure × maxBeta"
          value={agent.betaGZS.toFixed(4)}
          highlight={agent.betaGZS < 0.4}
        />
        <StatRow
          label="Risk Aversion λ"
          value={lambda.toFixed(2)}
        />
        <StatRow
          label="GZS Input"
          value={gzs.toFixed(4)}
          highlight={gzs >= 0.5}
        />
      </div>

      <div className="px-6 pb-4">
        <p className="text-[11px] text-zinc-400 dark:text-zinc-600 leading-relaxed">
          Exposure adjusts continuously each epoch. At GZS&nbsp;≥&nbsp;0.5 the
          efficient frontier shifts — rational agents reduce LST exposure without
          external enforcement.
        </p>
      </div>
    </div>
  );
}
