import type { EpochStatus } from "@/lib/types";

const IPFS_GATEWAY = "https://gateway.pinata.cloud/ipfs/";
const FILECOIN_GATEWAY = "https://gateway.lighthouse.storage/ipfs/";

function truncateCid(cid: string) {
  return `${cid.slice(0, 10)}…${cid.slice(-6)}`;
}

function Layer({
  label,
  dot,
  cid,
  href,
  statusText,
}: {
  label: string;
  dot: "green" | "amber" | "zinc";
  cid?: string;
  href?: string;
  statusText?: string;
}) {
  const dotClass =
    dot === "green"
      ? "bg-emerald-500"
      : dot === "amber"
      ? "bg-amber-400 animate-pulse"
      : "bg-zinc-300 dark:bg-zinc-600";

  return (
    <div className="flex items-center gap-2">
      <span className={`h-1.5 w-1.5 rounded-full flex-shrink-0 ${dotClass}`} />
      <span className="text-xs text-zinc-500 dark:text-zinc-400 font-medium">{label}</span>
      {cid && href ? (
        <a
          href={href}
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs font-mono text-indigo-500 dark:text-indigo-400 hover:text-indigo-700 dark:hover:text-indigo-300 hover:underline transition-colors"
          title={cid}
        >
          {truncateCid(cid)} ↗
        </a>
      ) : (
        <span className="text-xs text-zinc-400 dark:text-zinc-600">{statusText ?? "—"}</span>
      )}
    </div>
  );
}

export function StorageProof({ epoch }: { epoch: EpochStatus }) {
  return (
    <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-sm px-5 py-3">
      <div className="flex items-center flex-wrap gap-x-6 gap-y-2">
        <span className="text-xs font-semibold text-zinc-400 dark:text-zinc-500 uppercase tracking-widest flex-shrink-0">
          Persistence
        </span>
        <Layer label="Firestore" dot="green" statusText="Live" />
        <Layer
          label="IPFS"
          dot={epoch.ipfs_cid ? "green" : "amber"}
          cid={epoch.ipfs_cid}
          href={epoch.ipfs_cid ? `${IPFS_GATEWAY}${epoch.ipfs_cid}` : undefined}
          statusText="indexing…"
        />
        <Layer
          label="Filecoin"
          dot={epoch.filecoin_cid ? "green" : "amber"}
          cid={epoch.filecoin_cid}
          href={epoch.filecoin_cid ? `${FILECOIN_GATEWAY}${epoch.filecoin_cid}` : undefined}
          statusText="pending…"
        />
      </div>
    </div>
  );
}
