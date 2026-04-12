import type { EpochStatus } from "@/lib/types";
import { RiskBadge } from "./RiskBadge";

function Stat({
  label,
  value,
  className,
}: {
  label: string;
  value: string;
  className?: string;
}) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-xs text-zinc-500 uppercase tracking-wide">{label}</span>
      <span
        className={`text-sm font-mono font-medium text-zinc-900 dark:text-zinc-100 ${className ?? ""}`.trim()}
      >
        {value}
      </span>
    </div>
  );
}

interface Props {
  epoch: EpochStatus;
  snapshotAgeSeconds?: number | null;
}

export function EpochHeader({ epoch, snapshotAgeSeconds }: Props) {
  const hasTimezone = /Z|[+-]\d{2}:\d{2}$/.test(epoch.timestamp);
  const epochDate = new Date(hasTimezone ? epoch.timestamp : `${epoch.timestamp}Z`);
  const ts = epochDate.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    timeZone: "UTC",
  });

  const ageDisplay = (() => {
    if (snapshotAgeSeconds === null || snapshotAgeSeconds === undefined) return "—";
    const hours = Math.floor(snapshotAgeSeconds / 3600);
    const minutes = Math.floor((snapshotAgeSeconds % 3600) / 60);
    const seconds = snapshotAgeSeconds % 60;
    if (hours > 0) return `${hours}h ${minutes}m`;
    if (minutes > 0) return `${minutes}m ${seconds}s`;
    return `${seconds}s`;
  })();

  const pollIntervalSeconds = Number(
    process.env.NEXT_PUBLIC_POLL_INTERVAL_SECONDS ?? 60
  );
  const isStale =
    snapshotAgeSeconds !== null &&
    snapshotAgeSeconds !== undefined &&
    snapshotAgeSeconds > pollIntervalSeconds * 2;
  const staleClass = isStale ? "text-amber-600 dark:text-amber-400" : "";

  const score = epoch.risk.grey_zone_score;
  const scoreDisplay =
    score === Infinity || score > 999 ? "∞" : score.toFixed(4);

  return (
    <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 px-6 py-4 shadow-sm">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-3">
          <h2 className="text-lg font-bold text-zinc-900 dark:text-zinc-50">
            Epoch{" "}
            <span className="font-mono">{epoch.epoch.toLocaleString()}</span>
          </h2>
          <RiskBadge level={epoch.risk.risk_level} />
          {epoch.is_grey_zone && (
            <span className="text-xs font-semibold text-amber-600 animate-pulse">
              GREY ZONE ACTIVE
            </span>
          )}
        </div>
        <div className="flex flex-wrap gap-6">
          <Stat label="Block" value={epoch.block_number.toLocaleString()} />
          <Stat label="Time (UTC)" value={ts} />
          <Stat
            label="Validators"
            value={epoch.total_validators.toLocaleString()}
          />
          <Stat
            label="Participation"
            value={`${(epoch.participation_rate * 100).toFixed(2)}%`}
          />
          <Stat
            label="Grey Zone Score"
            value={scoreDisplay}
          />
          <Stat
            label="Last update"
            value={ageDisplay}
            className={staleClass}
          />
          <Stat
            label="Lido TVL"
            value={`${epoch.lido_tvl_eth.toLocaleString(undefined, { maximumFractionDigits: 0 })} ETH`}
          />
        </div>
      </div>
    </div>
  );
}
