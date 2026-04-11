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

interface Props {
  epoch: EpochStatus;
}

export function RiskTable({ epoch }: Props) {
  const r = epoch.risk;

  const rows: { label: string; value: string; highlight?: boolean }[] = [
    {
      label: "Risk Level",
      value: "",           // rendered as badge below
    },
    {
      label: "Grey Zone Score",
      value: r.grey_zone_score > 999 ? "∞" : fmt(r.grey_zone_score),
      highlight: r.risk_level !== "HEALTHY",
    },
    {
      label: "Gross Slashing Loss",
      value: fmtEth(r.gross_slashing_loss_eth),
      highlight: r.gross_slashing_loss_eth > 0,
    },
    {
      label: "CL Rewards",
      value: r.has_rewards_data ? fmtEth(r.cl_rewards_eth) : "pending…",
    },
    {
      label: "Burned ETH (EIP-1559)",
      value: fmtEth(r.burned_eth),
    },
    {
      label: "Slashed Validators",
      value: epoch.slashed_validators.toString(),
      highlight: epoch.slashed_validators > 0,
    },
    {
      label: "Slashing Penalty",
      value: fmtEth(epoch.slashing_penalty_eth),
    },
    {
      label: "Net Rebase",
      value: fmtEth(epoch.net_rebase_eth),
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
              <td className="px-6 py-2.5 text-zinc-500 dark:text-zinc-400 w-1/2">
                {row.label}
              </td>
              <td
                className={`px-6 py-2.5 font-mono font-medium text-right ${
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
