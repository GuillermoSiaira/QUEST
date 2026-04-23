import type { EpochStatus } from "@/lib/types";
import { RiskBadge } from "./RiskBadge";

function fmt(value: number | null, decimals = 4): string {
  if (value === null) return "—";
  return value.toFixed(decimals);
}

function fmtEth(value: number | null): string {
  if (value === null) return "—";
  return `${value.toFixed(4)} ETH`;
}

// Epochs per year: 365.25 days × 86400 s/day ÷ 384 s/epoch ≈ 82125
const EPOCHS_PER_YEAR = (365.25 * 86400) / (32 * 12);

function impliedApy(clRewardsEth: number, totalActiveBalanceEth: number): string {
  if (!isFinite(clRewardsEth) || totalActiveBalanceEth <= 0) return "—";
  const apy = (clRewardsEth / totalActiveBalanceEth) * EPOCHS_PER_YEAR * 100;
  return `${apy.toFixed(2)}%`;
}

interface Props {
  epoch: EpochStatus;
}

export function RiskTable({ epoch }: Props) {
  const r = epoch.risk;

  const rows: {
    label: string;
    value: string;
    sub?: string;
    highlight?: boolean;
  }[] = [
    {
      label: "Risk Level",
      value: "",           // rendered as badge below
    },
    {
      label: "Grey Zone Score",
      value: r.grey_zone_score > 999 ? "∞" : fmt(r.grey_zone_score),
      sub: "gross loss / (CL rewards + EL activity)",
      highlight: r.risk_level !== "HEALTHY",
    },
    {
      label: "Gross Slashing Loss",
      value: fmtEth(r.gross_slashing_loss_eth),
      sub: "initial + midterm penalty (consensus spec)",
      highlight: r.gross_slashing_loss_eth > 0,
    },
    {
      label: "CL Rewards",
      value: r.has_rewards_data ? fmtEth(r.cl_rewards_eth) : "pending…",
      sub: r.has_rewards_data
        ? `network aggregate · implied ${impliedApy(r.cl_rewards_eth, epoch.total_active_balance_eth)} APY`
        : "first poll — baseline pending",
    },
    {
      label: "EL Block Burn",
      value: fmtEth(r.burned_eth),
      sub: "EIP-1559 base fee · proxy for EL activity (not MEV)",
    },
    {
      label: "Slashed Validators",
      value: epoch.slashed_validators.toString(),
      highlight: epoch.slashed_validators > 0,
    },
    {
      label: "Slashing Penalty",
      value: fmtEth(epoch.slashing_penalty_eth),
      sub: "initial: 1 ETH × n_slashed (pre-Electra)",
    },
    {
      label: "Net Rebase",
      value: fmtEth(epoch.net_rebase_eth),
      sub: "CL rewards − slashing penalty",
      highlight:
        epoch.net_rebase_eth !== null && epoch.net_rebase_eth < 0,
    },
    {
      label: "Total Active Balance",
      value: `${(epoch.total_active_balance_eth / 1e6).toFixed(2)}M ETH`,
    },
    {
      label: "Gas Price",
      value: `${epoch.avg_gas_price_gwei.toFixed(2)} Gwei`,
    },
  ];

  return (
    <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-sm overflow-hidden">
      <div className="px-6 py-3 border-b border-zinc-100 dark:border-zinc-800">
        <h3 className="text-sm font-semibold text-zinc-700 dark:text-zinc-300 uppercase tracking-wide">
          Epoch Risk Breakdown
        </h3>
      </div>
      <table className="w-full text-sm">
        <tbody>
          {rows.map((row) => (
            <tr
              key={row.label}
              className="border-b border-zinc-50 dark:border-zinc-800/50 last:border-0"
            >
              <td className="px-6 py-2.5 w-1/2">
                <div className="flex flex-col">
                  <span className="text-zinc-500 dark:text-zinc-400">{row.label}</span>
                  {row.sub && (
                    <span className="text-[10px] text-zinc-400 dark:text-zinc-600">
                      {row.sub}
                    </span>
                  )}
                </div>
              </td>
              <td
                className={`px-6 py-2.5 font-mono font-medium text-right align-top ${
                  row.highlight
                    ? "text-red-600 dark:text-red-400"
                    : "text-zinc-900 dark:text-zinc-100"
                }`}
              >
                {row.label === "Risk Level" ? (
                  <div className="flex justify-end">
                    <RiskBadge level={r.risk_level} />
                  </div>
                ) : (
                  row.value
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
