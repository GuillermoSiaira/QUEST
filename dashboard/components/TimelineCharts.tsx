"use client";

import {
  ResponsiveContainer,
  ComposedChart,
  LineChart,
  BarChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  CartesianGrid,
} from "recharts";
import type { EpochStatus } from "@/lib/types";

interface Props {
  history: EpochStatus[];
}

const TICK_STYLE = { fontSize: 10, fill: "#71717a" };
const GRID_STYLE = { stroke: "#27272a", strokeDasharray: "3 3" };

function xFormatter(epoch: number) {
  return `#${epoch}`;
}

function Panel({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <p className="text-xs font-semibold text-zinc-500 dark:text-zinc-400 uppercase tracking-wide mb-1 px-1">
        {title}
      </p>
      {children}
    </div>
  );
}

export function TimelineCharts({ history }: Props) {
  if (history.length === 0) {
    return (
      <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 px-6 py-8 shadow-sm flex items-center justify-center text-zinc-400 text-sm">
        Waiting for history data…
      </div>
    );
  }

  const data = history.map((s) => ({
    epoch: s.epoch,
    score: Math.min(s.risk.grey_zone_score === Infinity ? 2 : s.risk.grey_zone_score, 2),
    participation: +(s.participation_rate * 100).toFixed(3),
    slashed: s.slashed_validators,
    cl_rewards: +s.risk.cl_rewards_eth.toFixed(4),
    slashing_loss: +s.risk.gross_slashing_loss_eth.toFixed(4),
  }));

  const n = history.length;

  return (
    <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-sm px-4 pt-4 pb-3 flex flex-col gap-5">
      <div className="flex items-center justify-between px-1">
        <h3 className="text-sm font-semibold text-zinc-700 dark:text-zinc-300 uppercase tracking-wide">
          Timeline
        </h3>
        <span className="text-xs text-zinc-400">{n} epoch{n !== 1 ? "s" : ""}</span>
      </div>

      {/* Chart 1: Grey Zone Score */}
      <Panel title="Grey Zone Score">
        <ResponsiveContainer width="100%" height={140}>
          <ComposedChart data={data} margin={{ top: 4, right: 12, left: -16, bottom: 0 }}>
            <CartesianGrid {...GRID_STYLE} />
            <XAxis dataKey="epoch" tick={TICK_STYLE} tickLine={false} axisLine={false} tickFormatter={xFormatter} />
            <YAxis domain={[0, 2]} tick={TICK_STYLE} tickLine={false} axisLine={false} tickCount={5} />
            <Tooltip
              contentStyle={{ fontSize: 11, borderRadius: 6, border: "1px solid #3f3f46", background: "#18181b" , color: "#e4e4e7"}}
              formatter={(v) => [(Number(v) || 0).toFixed(4), "Score"]}
              labelFormatter={(l) => `Epoch #${l}`}
            />
            <ReferenceLine y={0.5} stroke="#f59e0b" strokeDasharray="4 2" label={{ value: "Grey Zone", fontSize: 8, fill: "#f59e0b", position: "insideTopRight" }} />
            <ReferenceLine y={1.0} stroke="#ef4444" strokeDasharray="4 2" label={{ value: "Critical", fontSize: 8, fill: "#ef4444", position: "insideTopRight" }} />
            <Line type="monotone" dataKey="score" stroke="#6366f1" strokeWidth={2} dot={n < 20} activeDot={{ r: 4 }} />
          </ComposedChart>
        </ResponsiveContainer>
      </Panel>

      {/* Chart 2: Participation Rate */}
      <Panel title="Participation Rate (%)">
        <ResponsiveContainer width="100%" height={110}>
          <LineChart data={data} margin={{ top: 4, right: 12, left: -16, bottom: 0 }}>
            <CartesianGrid {...GRID_STYLE} />
            <XAxis dataKey="epoch" tick={TICK_STYLE} tickLine={false} axisLine={false} tickFormatter={xFormatter} />
            <YAxis domain={[90, 100]} tick={TICK_STYLE} tickLine={false} axisLine={false} tickCount={4} unit="%" />
            <Tooltip
              contentStyle={{ fontSize: 11, borderRadius: 6, border: "1px solid #3f3f46", background: "#18181b", color: "#e4e4e7" }}
              formatter={(v) => [`${(Number(v) || 0).toFixed(3)}%`, "Participation"]}
              labelFormatter={(l) => `Epoch #${l}`}
            />
            <ReferenceLine y={95} stroke="#f59e0b" strokeDasharray="4 2" label={{ value: "95%", fontSize: 8, fill: "#f59e0b", position: "insideTopRight" }} />
            <Line type="monotone" dataKey="participation" stroke="#10b981" strokeWidth={2} dot={n < 20} activeDot={{ r: 4 }} />
          </LineChart>
        </ResponsiveContainer>
      </Panel>

      {/* Chart 3: Slashed Validators */}
      <Panel title="Slashed Validators">
        <ResponsiveContainer width="100%" height={100}>
          <BarChart data={data} margin={{ top: 4, right: 12, left: -16, bottom: 0 }}>
            <CartesianGrid {...GRID_STYLE} />
            <XAxis dataKey="epoch" tick={TICK_STYLE} tickLine={false} axisLine={false} tickFormatter={xFormatter} />
            <YAxis allowDecimals={false} tick={TICK_STYLE} tickLine={false} axisLine={false} tickCount={3} />
            <Tooltip
              contentStyle={{ fontSize: 11, borderRadius: 6, border: "1px solid #3f3f46", background: "#18181b", color: "#e4e4e7" }}
              formatter={(v) => [Number(v) || 0, "Slashed"]}
              labelFormatter={(l) => `Epoch #${l}`}
            />
            <Bar dataKey="slashed" fill="#ef4444" radius={[2, 2, 0, 0]} maxBarSize={16} />
          </BarChart>
        </ResponsiveContainer>
      </Panel>
    </div>
  );
}
