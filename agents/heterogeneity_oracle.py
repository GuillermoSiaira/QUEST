#!/usr/bin/env python3
"""
heterogeneity_oracle.py
───────────────────────
Computes Var / H(model_selection, t) for the Olas Mech ecosystem.

Pipeline:
  1. Fetch ALL Request events from Mech contract (Gnosis Chain)
  2. Map each requester wallet → service multisig → configHash → service type
  3. For each time window: compute Shannon entropy H(configHash distribution)
  4. Plot evolution + static snapshot
  5. Alert if H < H* (homogeneity threshold)

Mech Legacy Fixed Pricing: 0x77af31De935740567Cf4fF1986D04B2c964A786a
MechMarketplace:            0x4554fE75c1f5576c1d7F765B2A036c199Adae329
Request event topic0:       0x4bda649efe6b98b0f9c1d5e859c29e20910f45c66dabfe6fad4a4881f7faf9cc

Usage:
  python heterogeneity_oracle.py                    # fetch last 14 days + analyze
  python heterogeneity_oracle.py --days 30          # extend window
  python heterogeneity_oracle.py --skip-fetch       # use cached events
  python heterogeneity_oracle.py --hstar 0.5        # custom alert threshold
"""

import sys, os, json, asyncio, math, argparse
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent / "risk-engine"))
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

try:
    import aiohttp
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import numpy as np
except ImportError as e:
    print(f"ERROR: {e}\npip install aiohttp matplotlib numpy")
    sys.exit(1)

# ── Constants ─────────────────────────────────────────────────────────────────

GNOSIS_RPC = "https://rpc.gnosis.gateway.fm"
GNOSIS_RPC_ALT = "https://rpc.ankr.com/gnosis"

MECH_LEGACY   = "0x77af31De935740567Cf4fF1986D04B2c964A786a"
MECH_MARKET   = "0x4554fE75c1f5576c1d7F765B2A036c199Adae329"
MECHS = [MECH_LEGACY, MECH_MARKET]

# keccak256("Request(address,uint256,bytes)")
REQUEST_TOPIC = "0x4bda649efe6b98b0f9c1d5e859c29e20910f45c66dabfe6fad4a4881f7faf9cc"

# Known configHash → service type (from IPFS analysis)
KNOWN_CONFIGS: dict[str, str] = {
    "33e5d1f1dc62d53b74b2a8b5ff4cb9e12d5e6b4f8a7c3d091e2f4a6b8c0d2e4": "valory/trader/0.1.0",
    "470b569d088dae30b976": "valory/trader_pearl/0.1.0",  # partial — will partial-match
}

# Gnosis block time ~5.3 seconds average
BLOCKS_PER_DAY = int(86400 / 5.3)

DATA_DIR = Path(__file__).parent
EVENTS_CACHE = DATA_DIR / "mech_events_cache.json"
OUT_DIR = DATA_DIR

# ── RPC helpers ───────────────────────────────────────────────────────────────

async def rpc_call(session: aiohttp.ClientSession, url: str, method: str,
                   params: list, req_id: int = 1) -> dict:
    payload = {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params}
    for attempt in range(4):
        try:
            async with session.post(url, json=payload,
                                    timeout=aiohttp.ClientTimeout(total=30)) as r:
                data = await r.json(content_type=None)
                if "error" in data:
                    if attempt < 3:
                        await asyncio.sleep(2 ** attempt)
                        continue
                return data
        except Exception as e:
            if attempt == 3:
                return {"error": str(e)}
            await asyncio.sleep(2 ** attempt)
    return {"error": "max retries"}


async def get_block_number(session: aiohttp.ClientSession, url: str) -> int:
    resp = await rpc_call(session, url, "eth_blockNumber", [])
    return int(resp.get("result", "0x0"), 16)


async def get_block_timestamp(session: aiohttp.ClientSession, url: str,
                              block_hex: str) -> int:
    resp = await rpc_call(session, url, "eth_getBlockByNumber", [block_hex, False])
    blk = resp.get("result", {}) or {}
    ts = blk.get("timestamp", "0x0")
    return int(ts, 16)


async def get_logs_range(session: aiohttp.ClientSession, url: str,
                         from_block: int, to_block: int,
                         address: str, topic: str) -> list[dict]:
    """Fetch eth_getLogs for a block range, returns raw log dicts."""
    resp = await rpc_call(session, url, "eth_getLogs", [{
        "fromBlock": hex(from_block),
        "toBlock":   hex(to_block),
        "address":   address,
        "topics":    [topic],
    }])
    if "error" in resp:
        return []
    return resp.get("result", [])

# ── Event fetching ────────────────────────────────────────────────────────────

def parse_request_event(log: dict) -> dict | None:
    """
    Event: Request(address indexed sender, uint256 requestId, bytes data)
    topics[0] = event sig
    topics[1] = sender (address, padded)  — only sender is indexed
    data = ABI-encoded (uint256 requestId, bytes data)
    """
    topics = log.get("topics", [])
    if len(topics) < 2:
        return None
    sender = "0x" + topics[1][-40:]
    block_num = int(log.get("blockNumber", "0x0"), 16)
    tx_hash = log.get("transactionHash", "")
    return {
        "sender": sender.lower(),
        "block": block_num,
        "tx": tx_hash,
        "mech": log.get("address", "").lower(),
    }


async def fetch_all_events(days: int = 14) -> list[dict]:
    """Fetch Request events from both Mech contracts for the last `days` days."""
    url = GNOSIS_RPC
    async with aiohttp.ClientSession() as session:
        current_block = await get_block_number(session, url)
        if current_block == 0:
            url = GNOSIS_RPC_ALT
            current_block = await get_block_number(session, url)
        print(f"  Current Gnosis block: {current_block:,}  RPC: {url}")

        blocks_back = days * BLOCKS_PER_DAY
        from_block  = current_block - blocks_back
        print(f"  Fetching from block {from_block:,} ({days} days back)")

        # Fetch block timestamps for first and last block
        ts_from = await get_block_timestamp(session, url, hex(from_block))
        ts_to   = await get_block_timestamp(session, url, hex(current_block))
        print(f"  Window: {datetime.fromtimestamp(ts_from, tz=timezone.utc).date()} → "
              f"{datetime.fromtimestamp(ts_to, tz=timezone.utc).date()}")

        STEP = 10_000  # 10k blocks per batch works on Gnosis public RPC
        all_events: list[dict] = []
        total_blocks = current_block - from_block
        batch_ranges = list(range(from_block, current_block, STEP))
        print(f"  {len(batch_ranges)} batches × {len(MECHS)} contracts")

        for i, start in enumerate(batch_ranges):
            end = min(start + STEP - 1, current_block)
            tasks = [get_logs_range(session, url, start, end, addr, REQUEST_TOPIC)
                     for addr in MECHS]
            results = await asyncio.gather(*tasks)
            for logs in results:
                for log in logs:
                    ev = parse_request_event(log)
                    if ev:
                        all_events.append(ev)
            if (i + 1) % 5 == 0 or i == 0 or i == len(batch_ranges) - 1:
                pct = (i + 1) / len(batch_ranges) * 100
                print(f"    batch {i+1}/{len(batch_ranges)} ({pct:.0f}%)  "
                      f"events: {len(all_events):,}")
            await asyncio.sleep(0.1)

        # Add approximate timestamps (interpolate linearly between from_block and current_block)
        block_range = current_block - from_block
        time_range  = ts_to - ts_from
        for ev in all_events:
            frac = (ev["block"] - from_block) / block_range if block_range else 0
            ev["timestamp"] = int(ts_from + frac * time_range)
            ev["date"] = datetime.fromtimestamp(ev["timestamp"], tz=timezone.utc).strftime("%Y-%m-%d")

        print(f"\n  Total events fetched: {len(all_events):,}")
        return all_events

# ── configHash mapping ────────────────────────────────────────────────────────

def build_wallet_to_config(svc_data: dict) -> dict[str, str]:
    """multisig address (lower) → config_hash"""
    m = {}
    for sid, d in svc_data.items():
        ms = d.get("multisig", "").lower()
        ch = d.get("config_hash", "")
        if ms and ch:
            m[ms] = ch
    return m


def classify_config(config_hash: str, ipfs_types: dict[str, str]) -> str:
    """Map config_hash to human-readable service type."""
    for known_hash, label in ipfs_types.items():
        if config_hash.startswith(known_hash[:20]):
            return label
    return config_hash[:12] + "..."

# ── Heterogeneity metrics ─────────────────────────────────────────────────────

def shannon_entropy(counts: dict) -> float:
    total = sum(counts.values())
    if total == 0:
        return 0.0
    probs = [v / total for v in counts.values() if v > 0]
    return -sum(p * math.log2(p) for p in probs)


def normalized_entropy(counts: dict) -> float:
    H = shannon_entropy(counts)
    n = len([v for v in counts.values() if v > 0])
    if n <= 1:
        return 0.0
    return H / math.log2(n)


def compute_daily_entropy(events: list[dict], wallet_to_config: dict,
                          ipfs_types: dict) -> dict[str, dict]:
    """Returns {date: {entropy, n_requests, n_configs, top_config_pct}}"""
    by_date: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for ev in events:
        ch = wallet_to_config.get(ev["sender"])
        if ch is None:
            ch = "__unknown__"
        label = classify_config(ch, ipfs_types)
        by_date[ev["date"]][label] += 1

    result = {}
    for date, counts in sorted(by_date.items()):
        n = sum(counts.values())
        top_pct = max(counts.values()) / n if n > 0 else 1.0
        result[date] = {
            "n_requests": n,
            "n_configs": len(counts),
            "H": shannon_entropy(counts),
            "H_norm": normalized_entropy(counts),
            "top_config_pct": top_pct,
            "counts": dict(counts),
        }
    return result

# ── Visualization ─────────────────────────────────────────────────────────────

def plot_heterogeneity(daily: dict[str, dict], hstar: float, out_path: Path):
    dates = [datetime.strptime(d, "%Y-%m-%d") for d in daily.keys()]
    h_norm = [v["H_norm"] for v in daily.values()]
    top_pct = [v["top_config_pct"] * 100 for v in daily.values()]
    n_req   = [v["n_requests"] for v in daily.values()]

    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
    fig.suptitle("Olas Mech — Heterogeneity Oracle\n"
                 "Morris-Shin diagnostic for agent model diversity",
                 fontsize=13, fontweight="bold")

    # ── Panel 1: normalized entropy ──
    ax1 = axes[0]
    ax1.fill_between(dates, h_norm, alpha=0.3, color="#3b82f6", label="H_norm(t)")
    ax1.plot(dates, h_norm, color="#3b82f6", linewidth=1.5)
    ax1.axhline(hstar, color="#ef4444", linestyle="--", linewidth=1.5,
                label=f"H* = {hstar:.2f} (alert threshold)")
    ax1.axhline(0, color="#6b7280", linewidth=0.5)
    ax1.axhline(1, color="#6b7280", linewidth=0.5, linestyle=":")
    ax1.set_ylabel("Normalized Entropy H_norm", fontsize=10)
    ax1.set_ylim(-0.05, 1.1)
    ax1.legend(fontsize=9)
    ax1.annotate("← Homogeneous", xy=(0.01, 0.03), xycoords="axes fraction",
                 fontsize=8, color="#6b7280")
    ax1.annotate("← Diverse", xy=(0.01, 0.88), xycoords="axes fraction",
                 fontsize=8, color="#6b7280")

    # Fill alert zone
    h_arr = np.array(h_norm)
    d_arr = np.array(dates)
    alert_mask = h_arr < hstar
    if alert_mask.any():
        ax1.fill_between(d_arr, 0, hstar, where=alert_mask,
                         alpha=0.15, color="#ef4444", label="Alert zone")

    # ── Panel 2: top config dominance ──
    ax2 = axes[1]
    ax2.fill_between(dates, top_pct, alpha=0.3, color="#f59e0b")
    ax2.plot(dates, top_pct, color="#f59e0b", linewidth=1.5,
             label="Top-1 configHash share (%)")
    ax2.axhline(100, color="#6b7280", linewidth=0.5, linestyle=":")
    ax2.set_ylabel("Dominant config share (%)", fontsize=10)
    ax2.set_ylim(0, 110)
    ax2.legend(fontsize=9)

    # ── Panel 3: request volume ──
    ax3 = axes[2]
    ax3.bar(dates, n_req, color="#10b981", alpha=0.7, label="Daily requests")
    ax3.set_ylabel("Requests / day", fontsize=10)
    ax3.legend(fontsize=9)

    ax3.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax3.xaxis.set_major_locator(mdates.DayLocator(interval=2))
    plt.xticks(rotation=30, ha="right")

    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"\n  Plot saved → {out_path}")


def plot_static_snapshot(events: list[dict], wallet_to_config: dict,
                         ipfs_types: dict, out_path: Path):
    """Bar chart of requests by configHash/service type (full window aggregate)."""
    counts: dict[str, int] = defaultdict(int)
    unknown = 0
    for ev in events:
        ch = wallet_to_config.get(ev["sender"])
        if ch is None:
            unknown += 1
            continue
        label = classify_config(ch, ipfs_types)
        counts[label] += 1

    if unknown:
        counts["__unknown__"] = unknown

    sorted_counts = sorted(counts.items(), key=lambda x: -x[1])
    labels = [x[0] for x in sorted_counts]
    values = [x[1] for x in sorted_counts]
    total  = sum(values)
    pcts   = [v / total * 100 for v in values]

    colors = ["#3b82f6", "#f59e0b", "#10b981", "#ef4444", "#8b5cf6",
              "#6b7280"] * (len(labels) // 6 + 1)

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(range(len(labels)), values, color=colors[:len(labels)])
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels([l[:25] for l in labels], rotation=35, ha="right", fontsize=8)
    ax.set_ylabel("Requests", fontsize=11)
    ax.set_title("Olas Mech — Request Distribution by Service Type\n"
                 f"Total: {total:,} requests  |  H_norm = "
                 f"{normalized_entropy(dict(zip(labels, values))):.3f}  "
                 f"(0 = perfectly homogeneous)",
                 fontsize=11, fontweight="bold")

    for bar, pct in zip(bars, pcts):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + total * 0.005,
                f"{pct:.1f}%", ha="center", va="bottom", fontsize=8, fontweight="bold")

    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"  Snapshot plot → {out_path}")

# ── Main ──────────────────────────────────────────────────────────────────────

def print_oracle_report(daily: dict, hstar: float, window_label: str):
    H_values = [v["H_norm"] for v in daily.values()]
    avg_H    = sum(H_values) / len(H_values) if H_values else 0
    min_H    = min(H_values) if H_values else 0
    last_H   = H_values[-1] if H_values else 0
    total_req = sum(v["n_requests"] for v in daily.values())

    print(f"\n{'═'*60}")
    print(f"  HETEROGENEITY ORACLE — {window_label}")
    print(f"{'═'*60}")
    print(f"  Period         : {min(daily)} → {max(daily)}")
    print(f"  Total requests : {total_req:,}")
    print(f"  Days analyzed  : {len(daily)}")
    print(f"  H* (threshold) : {hstar:.3f}")
    print(f"  Avg H_norm     : {avg_H:.4f}")
    print(f"  Min H_norm     : {min_H:.4f}  ← worst day")
    print(f"  Last H_norm    : {last_H:.4f}  ← current state")
    print(f"{'─'*60}")

    if last_H < hstar:
        print(f"  ⚠  ALERT: Current H_norm ({last_H:.3f}) < H* ({hstar:.3f})")
        print(f"     System is operating in HOMOGENEOUS mode.")
        print(f"     Morris-Shin risk: all agents will respond identically.")
    else:
        print(f"  ✓  OK: H_norm ({last_H:.3f}) ≥ H* ({hstar:.3f})")

    print(f"{'─'*60}")
    print(f"  {'Date':<12} {'Requests':>10} {'H_norm':>10} {'Top config %':>14}")
    for date, v in sorted(daily.items()):
        alert = "⚠" if v["H_norm"] < hstar else " "
        print(f"  {date:<12} {v['n_requests']:>10,} {v['H_norm']:>10.4f} "
              f"{v['top_config_pct']*100:>13.1f}% {alert}")
    print(f"{'═'*60}\n")


async def main_async(args):
    DATA_DIR.mkdir(exist_ok=True)

    # ── Load service data for wallet → configHash mapping ──
    svc_data_path = DATA_DIR / "olas_gnosis_service_data.json"
    if not svc_data_path.exists():
        print("ERROR: olas_gnosis_service_data.json not found. Run scan_olas_agents.py first.")
        sys.exit(1)
    with open(svc_data_path) as f:
        svc_data = json.load(f)

    wallet_to_config = build_wallet_to_config(svc_data)
    print(f"  Loaded service data: {len(svc_data):,} services, "
          f"{len(wallet_to_config):,} multisig addresses")

    # Known IPFS types for display (populated from previous analysis)
    ipfs_types: dict[str, str] = {
        "33e5d1f1dc62d53b": "valory/trader/0.1.0",
        "470b569d088dae30": "valory/trader_pearl/0.1.0",
        "7a8c4e2f1b9d6c3a": "lstolas/lst_service:0.1.0",
    }

    # ── Fetch or load events ──
    if args.skip_fetch and EVENTS_CACHE.exists():
        print(f"[LOAD] Reading {EVENTS_CACHE}...")
        with open(EVENTS_CACHE) as f:
            events = json.load(f)
        print(f"  Loaded {len(events):,} cached events")
    else:
        print(f"[FETCH] Querying Mech events ({args.days} days)...")
        events = await fetch_all_events(days=args.days)
        with open(EVENTS_CACHE, "w") as f:
            json.dump(events, f)
        print(f"  Cached → {EVENTS_CACHE}")

    if not events:
        print("ERROR: No events found. Check RPC or contract address.")
        sys.exit(1)

    # ── Analysis ──
    print("\n[ANALYZE] Computing heterogeneity metrics...")
    daily = compute_daily_entropy(events, wallet_to_config, ipfs_types)

    window_label = f"Mech ({args.days}d window)"
    print_oracle_report(daily, args.hstar, window_label)

    # ── Plots ──
    print("[PLOT] Generating charts...")
    plot_heterogeneity(daily, args.hstar,
                       OUT_DIR / "heterogeneity_timeseries.png")
    plot_static_snapshot(events, wallet_to_config, ipfs_types,
                         OUT_DIR / "heterogeneity_snapshot.png")

    print("\n  Done. Key output files:")
    print(f"    {OUT_DIR}/heterogeneity_timeseries.png")
    print(f"    {OUT_DIR}/heterogeneity_snapshot.png")
    print(f"    {EVENTS_CACHE}")


def main():
    p = argparse.ArgumentParser(
        description="Olas Mech Heterogeneity Oracle — Morris-Shin diagnostic")
    p.add_argument("--days", type=int, default=14,
                   help="Days of history to fetch (default: 14)")
    p.add_argument("--skip-fetch", action="store_true",
                   help="Load cached events instead of querying chain")
    p.add_argument("--hstar", type=float, default=0.4,
                   help="Alert threshold for normalized entropy (default: 0.4)")
    args = p.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
