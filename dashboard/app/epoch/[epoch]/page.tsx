"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import type { EpochStatus } from "@/lib/types";
import { RiskBadge } from "@/components/RiskBadge";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const IPFS_GATEWAY = "https://gateway.pinata.cloud/ipfs/";
const FILECOIN_VIEWER = "https://files.lighthouse.storage/viewFile/";

function Row({ label, value, mono = true }: { label: string; value: string; mono?: boolean }) {
  return (
    <tr className="border-b border-zinc-100 dark:border-zinc-800 last:border-0">
      <td className="py-2.5 pr-6 text-sm text-zinc-500 dark:text-zinc-400 whitespace-nowrap">{label}</td>
      <td className={`py-2.5 text-sm text-zinc-900 dark:text-zinc-100 ${mono ? "font-mono" : ""}`}>
        {value}
      </td>
    </tr>
  );
}

function CidLink({ label, cid, href }: { label: string; cid: string; href: string }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-xs text-zinc-400 uppercase tracking-widest font-medium">{label}</span>
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        className="text-sm font-mono text-indigo-500 hover:underline break-all"
      >
        {cid}
      </a>
    </div>
  );
}

export default function EpochPage() {
  const params = useParams<{ epoch: string }>();
  const epochNumber = Number(params.epoch);
  const [data, setData] = useState<EpochStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/api/epoch/${epochNumber}`)
      .then((r) => {
        if (!r.ok) throw new Error(`Epoch ${epochNumber} not found`);
        return r.json();
      })
      .then(setData)
      .catch((e) => setError(e.message));
  }, [epochNumber]);

  const handleDownload = () => {
    if (!data) return;
    const json = JSON.stringify(
      {
        schema: "quest-epoch-snapshot-v1",
        network: "mainnet",
        data,
      },
      null,
      2
    );
    const blob = new Blob([json], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `quest-epoch-${epochNumber}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950">
      <header className="border-b border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 px-6 py-3 flex items-center gap-3">
        <a href="/" className="text-sm font-bold text-zinc-900 dark:text-zinc-50 hover:opacity-70">
          QUEST
        </a>
        <span className="text-zinc-300 dark:text-zinc-700">/</span>
        <span className="text-sm text-zinc-500">Epoch {epochNumber}</span>
      </header>

      <main className="max-w-3xl mx-auto px-4 py-8">
        {error && (
          <div className="rounded-xl border border-red-200 bg-red-50 dark:bg-red-950/20 dark:border-red-900 px-5 py-4 text-sm text-red-700 dark:text-red-400">
            {error}
          </div>
        )}

        {!data && !error && (
          <div className="text-center py-16 text-zinc-400 text-sm">Loading epoch {epochNumber}…</div>
        )}

        {data && (
          <div className="flex flex-col gap-5">
            {/* Header */}
            <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 px-6 py-5 shadow-sm">
              <div className="flex items-center justify-between flex-wrap gap-4">
                <div className="flex items-center gap-3">
                  <h1 className="text-2xl font-bold font-mono text-zinc-900 dark:text-zinc-50">
                    Epoch {data.epoch.toLocaleString()}
                  </h1>
                  <RiskBadge level={data.risk.risk_level} />
                </div>
                <button
                  onClick={handleDownload}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium transition-colors"
                >
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  Download JSON
                </button>
              </div>
              <p className="mt-2 text-xs text-zinc-400 font-mono">
                {new Date(data.timestamp).toUTCString()}
              </p>
            </div>

            {/* Storage proof */}
            {(data.ipfs_cid || data.filecoin_cid) && (
              <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 px-6 py-5 shadow-sm flex flex-col gap-4">
                <h2 className="text-xs font-semibold text-zinc-400 uppercase tracking-widest">
                  Decentralized Storage Proof
                </h2>
                {data.ipfs_cid && (
                  <CidLink
                    label="IPFS (Pinata)"
                    cid={data.ipfs_cid}
                    href={`${IPFS_GATEWAY}${data.ipfs_cid}`}
                  />
                )}
                {data.filecoin_cid && (
                  <CidLink
                    label="Filecoin (Lighthouse)"
                    cid={data.filecoin_cid}
                    href={`${FILECOIN_VIEWER}${data.filecoin_cid}`}
                  />
                )}
              </div>
            )}

            {/* Epoch data */}
            <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-sm overflow-hidden">
              <div className="px-6 py-3 border-b border-zinc-100 dark:border-zinc-800">
                <h2 className="text-xs font-semibold text-zinc-400 uppercase tracking-widest">Consensus Layer</h2>
              </div>
              <table className="w-full px-6">
                <tbody className="divide-y divide-zinc-50 dark:divide-zinc-800/50">
                  <Row label="Block" value={data.block_number.toLocaleString()} />
                  <Row label="Validators" value={data.total_validators.toLocaleString()} />
                  <Row label="Total Active Balance" value={`${(data.total_active_balance_eth / 1e6).toFixed(2)}M ETH`} />
                  <Row label="Participation" value={`${(data.participation_rate * 100).toFixed(2)}%`} />
                  <Row label="CL Rewards" value={data.risk.has_rewards_data ? `${data.risk.cl_rewards_eth.toFixed(4)} ETH` : "pending"} />
                  <Row label="Slashed Validators" value={data.slashed_validators.toString()} />
                  <Row label="Slashing Penalty" value={`${data.slashing_penalty_eth.toFixed(4)} ETH`} />
                  <Row label="Net Rebase" value={data.net_rebase_eth !== null ? `${data.net_rebase_eth.toFixed(4)} ETH` : "—"} />
                </tbody>
              </table>
            </div>

            <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-sm overflow-hidden">
              <div className="px-6 py-3 border-b border-zinc-100 dark:border-zinc-800">
                <h2 className="text-xs font-semibold text-zinc-400 uppercase tracking-widest">Risk Assessment</h2>
              </div>
              <table className="w-full">
                <tbody className="divide-y divide-zinc-50 dark:divide-zinc-800/50">
                  <Row label="Grey Zone Score" value={data.risk.grey_zone_score.toFixed(6)} />
                  <Row label="Gross Slashing Loss" value={`${data.risk.gross_slashing_loss_eth.toFixed(4)} ETH`} />
                  <Row label="Burned ETH (EIP-1559)" value={`${data.burned_eth.toFixed(4)} ETH`} />
                  <Row label="Gas Price" value={`${data.avg_gas_price_gwei.toFixed(2)} Gwei`} />
                  <Row label="Lido TVL" value={`${data.lido_tvl_eth.toLocaleString(undefined, { maximumFractionDigits: 0 })} ETH`} />
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>

      <footer className="text-center py-6 text-xs text-zinc-400">
        QUEST — Macroprudential Oracle for the Ethereum Ecosystem
      </footer>
    </div>
  );
}
