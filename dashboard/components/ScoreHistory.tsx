"use client";

import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
} from "recharts";
import type { EpochStatus } from "@/lib/types";

interface ChartPoint {
  epoch: number;
  score: number;
}

interface Props {
  history: EpochStatus[];
}

export function ScoreHistory({ history }: Props) {
  if (history.length === 0) {
    return (
      <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 px-6 py-8 shadow-sm flex items-center justify-center text-zinc-400 text-sm">
        Waiting for data…
      </div>
    );
  }

  const data: ChartPoint[] = history.map((s) => ({
    epoch: s.epoch,
    score: Math.min(s.risk.grey_zone_score, 2), // cap at 2 for display
  }));

  return (
    <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-sm px-2 pt-4 pb-2">
      <div className="px-4 pb-3">
        <h3 className="text-sm font-semibold text-zinc-700 dark:text-zinc-300 uppercase tracking-wide">
          Grey Zone Score — Last {history.length} Epochs
        </h3>
      </div>
      <ResponsiveContainer width="100%" height={180}>
        <LineChart data={data} margin={{ top: 4, right: 16, left: -8, bottom: 0 }}>
          <XAxis
            dataKey="epoch"
            tick={{ fontSize: 10, fill: "#a1a1aa" }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v: number) => `#${v}`}
          />
          <YAxis
            domain={[0, 2]}
            tick={{ fontSize: 10, fill: "#a1a1aa" }}
            tickLine={false}
            axisLine={false}
            tickCount={5}
          />
          <Tooltip
            contentStyle={{
              fontSize: 12,
              borderRadius: 8,
              border: "1px solid #e4e4e7",
              background: "#fff",
            }}
            formatter={(value) => [(Number(value) || 0).toFixed(4), "Score"]}
            labelFormatter={(label) => `Epoch #${label}`}
          />
          {/* GREY_ZONE threshold at 0.5 */}
          <ReferenceLine
            y={0.5}
            stroke="#f59e0b"
            strokeDasharray="4 2"
            label={{ value: "Grey Zone", fontSize: 9, fill: "#f59e0b" }}
          />
          {/* CRITICAL threshold at 1.0 */}
          <ReferenceLine
            y={1.0}
            stroke="#ef4444"
            strokeDasharray="4 2"
            label={{ value: "Critical", fontSize: 9, fill: "#ef4444" }}
          />
          <Line
            type="monotone"
            dataKey="score"
            stroke="#6366f1"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
