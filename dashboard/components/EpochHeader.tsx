import type { EpochStatus } from "@/lib/types";
import { RiskBadge } from "./RiskBadge";

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-xs text-zinc-500 uppercase tracking-wide">{label}</span>
      <span className="text-sm font-mono font-medium text-zinc-900 dark:text-zinc-100">
        {value}
      </span>
    </div>
  );
}

interface Props {
  epoch: EpochStatus;
}

export function EpochHeader({ epoch }: Props) {
  const ts = new Date(epoch.timestamp).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });

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
            label="Lido TVL"
            value={`${epoch.lido_tvl_eth.toLocaleString(undefined, { maximumFractionDigits: 0 })} ETH`}
          />
        </div>
      </div>
    </div>
  );
}
