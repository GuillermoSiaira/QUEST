#!/usr/bin/env python3
"""
estimate_lambda.py
──────────────────
Empirical estimation of λ (risk aversion) from on-chain stETH holdings.

Pipeline:
  1. stETH/ETH price weekly series — DeFiLlama API (free, no key)
  2. Top stETH holders — Transfer event scan via Alchemy eth_getLogs
  3. Weekly balanceOf per wallet — Alchemy eth_call at block checkpoints
  4. Compute α̂(i,t) = steth_value / max_steth_value (rolling proxy)
  5. Compute λ̂(i,t) = (1−α̂)·2·E(R) / σ²(s(t))
  6. Compute Var(F̂(λ,t)) per week → test for May 2022 collapse

Output:
  lambda_estimates.csv  — weekly λ̂ per wallet
  f_lambda_variance.csv — weekly Var(F̂(λ,t)) and statistics
  f_lambda_variance.png — chart (if matplotlib available)

Usage:
  python estimate_lambda.py
  python estimate_lambda.py --wallets 50 --start 2021-06 --end 2023-06
  python estimate_lambda.py --skip-scan --holders-file top_holders.json
"""

import sys, io, os, json, time, math, csv, argparse, asyncio
from pathlib import Path
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent / "risk-engine"))
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

try:
    import aiohttp
except ImportError:
    print("ERROR: pip install aiohttp python-dotenv")
    sys.exit(1)

# ── Constants ─────────────────────────────────────────────────────────────────

STETH_ADDRESS   = "0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84"
ALCHEMY_URL     = os.getenv("ALCHEMY_HTTP_URL", "")
E_R             = 0.0075
SIGMA_BASE      = 0.05
K               = math.log(10)

# Known protocol contracts to exclude from holder analysis (not real agents)
EXCLUDE_CONTRACTS = {
    "0xdc24316b9ae028f1497c275eb9192a3ea0f67022",  # Curve stETH/ETH pool
    "0x828b154032950c8ff7cf8085d841723db2696056",  # Curve stETH/ETH ng
    "0x7f39c581f595b53c5cb19bd0b3f8da6c935e2ca0",  # wstETH
    "0xae7ab96520de3a18e5e111b5eaab095312d7fe84",  # stETH itself
    "0x1982b2f5814301d4e9a8b0201555376e62f82428",  # Aave stETH market
    "0x388c818ca8b9251b393131c08a736a67ccb19297",  # Lido withdrawal queue
    "0xb9d7934878b5fb9610b3fe8a5e441701f7ac8e18",  # Lido withdrawal vault
    "0x0000000000000000000000000000000000000000",  # null
}

# ── Block number helpers ──────────────────────────────────────────────────────

# Approximate: Ethereum ~12s per block post-Merge, ~13s pre-Merge
# Block 13,571,665 = 2021-11-01 (good reference)
# Block 15,537,394 = 2022-09-15 (Merge)
MERGE_BLOCK = 15_537_394
MERGE_TS    = 1663224179  # unix

def ts_to_block_approx(ts: int) -> int:
    """Convert unix timestamp to approximate block number."""
    if ts >= MERGE_TS:
        return MERGE_BLOCK + int((ts - MERGE_TS) / 12)
    # Pre-merge: ~13.2s average
    REF_BLOCK = 11_565_019  # 2021-01-01
    REF_TS    = 1609459200
    return REF_BLOCK + int((ts - REF_TS) / 13.2)

def weekly_checkpoints(start: str, end: str) -> list[tuple[str, int]]:
    """Return list of (YYYY-WW, block_number) weekly checkpoints."""
    s = datetime.strptime(start, "%Y-%m").replace(day=1, tzinfo=timezone.utc)
    e = datetime.strptime(end,   "%Y-%m").replace(day=1, tzinfo=timezone.utc)
    weeks = []
    current = s
    while current <= e:
        label = current.strftime("%Y-%m-%d")
        block = ts_to_block_approx(int(current.timestamp()))
        weeks.append((label, block))
        current += timedelta(weeks=1)
    return weeks

# ── DeFiLlama price series ────────────────────────────────────────────────────

async def _llama_chart(session, coin_id: str, start_ts: int, end_ts: int) -> dict[int, float]:
    """Fetch USD price series from DeFiLlama, returns {timestamp: price_usd}."""
    url = f"https://coins.llama.fi/chart/{coin_id}"
    # Note: 'end' param breaks DeFiLlama for long ranges — use span only
    span_weeks = max(10, (end_ts - start_ts) // (7 * 86400) + 4)
    params = {"start": start_ts, "span": span_weeks, "period": "1w"}
    try:
        async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=20)) as r:
            text = await r.text()
            data = json.loads(text)
        coins = data.get("coins", {})
        key = next((k for k in coins if k.lower() == coin_id.lower()), None)
        if not key:
            print(f"  [WARN] DeFiLlama: key not found for {coin_id}. Keys: {list(coins.keys())[:3]}")
            return {}
        pts = coins[key].get("prices", [])
        # Filter to requested range
        return {
            int(p["timestamp"]): p["price"]
            for p in pts
            if start_ts <= int(p["timestamp"]) <= end_ts + 7*86400
        }
    except Exception as e:
        print(f"  [WARN] DeFiLlama {coin_id}: {e}")
        return {}

async def fetch_steth_prices(session: aiohttp.ClientSession, start_ts: int, end_ts: int) -> dict[str, float]:
    """Returns {date_str: steth_eth_ratio} weekly — stETH_USD / ETH_USD."""
    steth_id = f"ethereum:{STETH_ADDRESS}"
    eth_id   = "coingecko:ethereum"

    steth_pts, eth_pts = await asyncio.gather(
        _llama_chart(session, steth_id, start_ts, end_ts),
        _llama_chart(session, eth_id,   start_ts, end_ts),
    )
    print(f"  stETH points: {len(steth_pts)}  ETH points: {len(eth_pts)}")

    prices = {}
    for ts, steth_usd in sorted(steth_pts.items()):
        if not eth_pts:
            break
        nearest = min(eth_pts, key=lambda t: abs(t - ts))
        eth_usd = eth_pts[nearest]
        if eth_usd > 0:
            date_str = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
            prices[date_str] = steth_usd / eth_usd
    return prices

# ── Alchemy JSON-RPC helpers ──────────────────────────────────────────────────

async def rpc_call(session: aiohttp.ClientSession, method: str, params: list, req_id: int = 1) -> dict:
    payload = {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params}
    for attempt in range(3):
        try:
            async with session.post(
                ALCHEMY_URL, json=payload,
                timeout=aiohttp.ClientTimeout(total=20)
            ) as r:
                return await r.json()
        except Exception as e:
            if attempt == 2:
                return {"error": str(e)}
            await asyncio.sleep(1.5 ** attempt)

async def rpc_batch(session: aiohttp.ClientSession, calls: list[dict]) -> list[dict]:
    """Execute a batch of RPC calls, returns list of results in order."""
    for attempt in range(3):
        try:
            async with session.post(
                ALCHEMY_URL, json=calls,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as r:
                results = await r.json()
            # Re-order by id
            by_id = {r["id"]: r for r in results if isinstance(r, dict)}
            return [by_id.get(c["id"], {"error": "missing"}) for c in calls]
        except Exception as e:
            if attempt == 2:
                return [{"error": str(e)}] * len(calls)
            await asyncio.sleep(1.5 ** attempt)

# ── Top holders scan ──────────────────────────────────────────────────────────

TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

async def scan_top_holders(
    session: aiohttp.ClientSession,
    n_wallets: int = 100,
    scan_start_block: int = 14_000_000,
    scan_end_block:   int = 15_000_000,
    max_pages: int = 200,
) -> list[str]:
    """
    Use alchemy_getAssetTransfers (Alchemy's own endpoint, no block-range limit)
    to find top stETH holders by net inflow in the scan window.
    """
    print(f"  Scanning via alchemy_getAssetTransfers blocks {scan_start_block}–{scan_end_block}...")
    net_flows: dict[str, float] = {}
    page_key = None
    pages = 0

    while pages < max_pages:
        params: dict = {
            "fromBlock": hex(scan_start_block),
            "toBlock":   hex(scan_end_block),
            "contractAddresses": [STETH_ADDRESS],
            "category":  ["erc20"],
            "withMetadata": False,
            "excludeZeroValue": True,
            "maxCount":  "0x3e8",  # 1000 per page
            "order":     "asc",
        }
        if page_key:
            params["pageKey"] = page_key

        resp = await rpc_call(session, "alchemy_getAssetTransfers", [params])
        result = resp.get("result", {})
        if "error" in resp:
            print(f"  [ERROR] alchemy_getAssetTransfers: {resp['error']}")
            break

        transfers = result.get("transfers", [])
        for t in transfers:
            frm    = (t.get("from") or "").lower()
            to     = (t.get("to")   or "").lower()
            amount = float(t.get("value") or 0)
            if frm not in EXCLUDE_CONTRACTS:
                net_flows[frm] = net_flows.get(frm, 0) - amount
            if to not in EXCLUDE_CONTRACTS:
                net_flows[to]  = net_flows.get(to, 0) + amount

        pages += 1
        page_key = result.get("pageKey")
        if pages % 20 == 0:
            print(f"    ... page {pages}, {len(net_flows)} wallets seen")
        if not page_key:
            break
        await asyncio.sleep(0.05)

    print(f"  Scanned {pages} pages, {len(net_flows)} wallets seen")
    candidates = {
        addr: flow
        for addr, flow in net_flows.items()
        if flow > 1.0 and addr not in EXCLUDE_CONTRACTS
    }
    top = sorted(candidates, key=lambda a: candidates[a], reverse=True)[:n_wallets]
    print(f"  Top {len(top)} holders (net inflow > 1 stETH in scan window)")
    return top

# ── Historical balances ───────────────────────────────────────────────────────

BALANCE_OF_SIG = "0x70a08231"  # balanceOf(address)

def encode_balance_of(wallet: str) -> str:
    addr = wallet.lower().replace("0x", "").zfill(64)
    return BALANCE_OF_SIG + addr

async def get_balances_at_blocks(
    session: aiohttp.ClientSession,
    wallets: list[str],
    checkpoints: list[tuple[str, int]],
    batch_size: int = 30,
) -> dict[str, dict[str, float]]:
    """
    Returns {wallet: {date: balance_eth}} for all wallets at all checkpoints.
    Uses JSON-RPC batching.
    """
    results: dict[str, dict[str, float]] = {w: {} for w in wallets}
    total = len(wallets) * len(checkpoints)
    done = 0

    # Build all calls
    all_calls = []
    call_meta = []  # (wallet, date)
    for date_str, block in checkpoints:
        for wallet in wallets:
            call_id = len(all_calls)
            all_calls.append({
                "jsonrpc": "2.0",
                "id": call_id,
                "method": "eth_call",
                "params": [{
                    "to":   STETH_ADDRESS,
                    "data": encode_balance_of(wallet),
                }, hex(block)],
            })
            call_meta.append((wallet, date_str))

    # Execute in batches
    for i in range(0, len(all_calls), batch_size):
        batch = all_calls[i:i+batch_size]
        meta  = call_meta[i:i+batch_size]
        resp  = await rpc_batch(session, batch)

        for (wallet, date_str), r in zip(meta, resp):
            raw = r.get("result", "0x")
            try:
                bal = int(raw, 16) / 1e18
            except:
                bal = 0.0
            results[wallet][date_str] = bal

        done += len(batch)
        if done % (batch_size * 5) == 0:
            pct = done / total * 100
            print(f"    ... {done}/{total} balance calls ({pct:.0f}%)")
        await asyncio.sleep(0.02)

    return results

# ── Lambda computation ────────────────────────────────────────────────────────

def sigma_sq(s: float) -> float:
    """Endogenous variance: σ²(s) = σ_base²·exp(k·s)."""
    return SIGMA_BASE**2 * math.exp(K * max(0.0, s))

def _nearest_price(prices: dict[str, float], date_str: str, max_days: int = 5) -> float | None:
    """Find closest price within max_days of date_str."""
    from datetime import date as date_type
    target = datetime.strptime(date_str, "%Y-%m-%d").date()
    best, best_delta = None, max_days + 1
    for d_str, p in prices.items():
        try:
            d = datetime.strptime(d_str, "%Y-%m-%d").date()
            delta = abs((d - target).days)
            if delta < best_delta:
                best, best_delta = p, delta
        except:
            pass
    return best

def compute_alpha_series(
    balances: dict[str, dict[str, float]],
    prices: dict[str, float],
    checkpoints: list[tuple[str, int]],
    rolling_window: int = 12,
) -> tuple[list[dict], list[dict]]:
    """
    Opción C — Preferencia revelada directa: mide Var(α̂(t)) sin pasar por λ̂.

    α̂(i,t) = stETH_balance(i,t) / max_balance(i, t-12w:t)
    Interpretación: fracción del "máximo histórico reciente" que el agente mantiene.
    Cuando α̂ cae → el agente redujo exposición → reveló mayor aversión.
    Var(α̂(t)) entre wallets → heterogeneidad de comportamiento.
    Colapso de Var(α̂) → homogeneización → bank run risk.

    También computa λ̂ cuando hay precio disponible, para comparación.
    """
    from collections import defaultdict
    dates = [d for d, _ in checkpoints]

    alpha_rows = []
    for i, (date_str, _) in enumerate(checkpoints):
        # Nearest stETH/ETH price (±5 days)
        price = _nearest_price(prices, date_str)
        s = (1.0 - price) if price is not None else None
        sig2 = sigma_sq(s) if s is not None else None

        for wallet, hist in balances.items():
            bal = hist.get(date_str, 0.0)
            if bal <= 0.001:
                continue

            # α̂: fraction of rolling-max balance retained
            window_bals = [hist.get(dates[j], 0.0)
                           for j in range(max(0, i - rolling_window + 1), i + 1)]
            max_bal = max(window_bals) if window_bals else bal
            alpha_hat = min(1.0, bal / max_bal) if max_bal > 0.001 else 1.0

            # λ̂ only when price is available (for reference)
            lam_hat = None
            if sig2 and sig2 > 0 and alpha_hat > 0.001:
                lam_hat = min(E_R / (alpha_hat * sig2), 15.0)

            alpha_rows.append({
                "date":          date_str,
                "wallet":        wallet[:10] + "...",
                "steth_balance": round(bal, 4),
                "alpha_hat":     round(alpha_hat, 4),
                "signal_s":      round(s, 6) if s is not None else None,
                "lambda_hat":    round(lam_hat, 4) if lam_hat is not None else None,
            })

    # Aggregate per week: Var(α̂) — the primary metric
    by_date_alpha = defaultdict(list)
    by_date_lam   = defaultdict(list)
    by_date_sig   = {}
    for row in alpha_rows:
        by_date_alpha[row["date"]].append(row["alpha_hat"])
        if row["lambda_hat"] is not None:
            by_date_lam[row["date"]].append(row["lambda_hat"])
        if row["signal_s"] is not None:
            by_date_sig[row["date"]] = row["signal_s"]

    def _stats(vals):
        n = len(vals)
        if n < 2:
            return n, 0.0, 0.0, 0.0
        mean = sum(vals) / n
        var  = sum((v - mean)**2 for v in vals) / n
        return n, round(mean, 4), round(math.sqrt(var), 4), round(var, 4)

    fvar_rows = []
    for date_str in sorted(by_date_alpha):
        alphas = by_date_alpha[date_str]
        if len(alphas) < 3:
            continue
        n_a, mean_a, std_a, var_a = _stats(alphas)

        lams = by_date_lam.get(date_str, [])
        _, mean_l, std_l, var_l = _stats(lams) if lams else (0, None, None, None)

        fvar_rows.append({
            "date":       date_str,
            "n_wallets":  n_a,
            "mean_alpha": mean_a,
            "std_alpha":  std_a,
            "var_alpha":  var_a,       # PRIMARY METRIC
            "mean_lambda": mean_l,
            "var_lambda":  var_l,      # secondary, only when price available
            "signal_s":   by_date_sig.get(date_str),
        })

    return alpha_rows, fvar_rows

# ── Output ────────────────────────────────────────────────────────────────────

def write_csv(rows: list[dict], path: Path):
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"  CSV → {path}")

def print_fvar_report(fvar_rows: list[dict]):
    sep = "─" * 95
    print()
    print(sep)
    print("  Var(α̂(t)) — Revealed Preference Heterogeneity over time")
    print("  PRIMARY METRIC: Var(α̂) = dispersion of retained-fraction across wallets")
    print(sep)
    print(f"  {'Date':>10}  {'N':>4}  {'mean_α':>7}  {'std_α':>7}  {'var_α':>7}  {'signal_s':>9}  note")
    print(sep)
    for r in fvar_rows:
        flag = "  ← DEPEG" if r["date"] and "2022-05" <= r["date"] <= "2022-07" else ""
        sig_str = f"{r['signal_s']:>9.4f}" if r["signal_s"] is not None else f"{'n/a':>9}"
        print(
            f"  {r['date']:>10}  {r['n_wallets']:>4}  "
            f"{r['mean_alpha']:>7.3f}  {r['std_alpha']:>7.3f}  "
            f"{r['var_alpha']:>7.4f}  {sig_str}{flag}"
        )
    print(sep)

    depeg = [r for r in fvar_rows if r["date"] and "2022-05" <= r["date"] <= "2022-07"]
    pre   = [r for r in fvar_rows if r["date"] and "2021-10" <= r["date"] <= "2022-04"]
    post  = [r for r in fvar_rows if r["date"] and "2022-08" <= r["date"] <= "2022-12"]

    if depeg and pre:
        min_depeg = min(r["var_alpha"] for r in depeg)
        avg_pre   = sum(r["var_alpha"] for r in pre) / len(pre)
        avg_post  = sum(r["var_alpha"] for r in post) / len(post) if post else None
        print(f"\n  Pre-depeg  avg Var(α̂): {avg_pre:.4f}  (n={len(pre)} weeks)")
        print(f"  Depeg      min Var(α̂): {min_depeg:.4f}  (n={len(depeg)} weeks)")
        if avg_post:
            print(f"  Post-depeg avg Var(α̂): {avg_post:.4f}  (n={len(post)} weeks)")
        if avg_pre > 0:
            pct = (avg_pre - min_depeg) / avg_pre * 100
            print(f"\n  Heterogeneity collapse: {pct:.1f}% reduction during depeg")
            print(f"  Interpretation: wallets homogenized behavior → coordinated exit")
    print()

def plot_fvar(fvar_rows: list[dict], path: Path):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
    except ImportError:
        print("  matplotlib not installed — skipping chart")
        return

    dates  = [r["date"]      for r in fvar_rows]
    var_a  = [r["var_alpha"] for r in fvar_rows]
    mean_a = [r["mean_alpha"] for r in fvar_rows]
    sig_s  = [r["signal_s"] if r["signal_s"] is not None else 0 for r in fvar_rows]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 8), sharex=True)
    fig.suptitle(
        "Revealed Preference Heterogeneity in stETH Holdings: Var(α̂(t))\n"
        "Hypothesis: Var(α̂) collapses during stress → homogenization → coordinated exit",
        fontsize=12, fontweight="bold"
    )

    xs = list(range(len(dates)))
    depeg_xs = [i for i, d in enumerate(dates) if "2022-05" <= d <= "2022-07"]

    # Panel 1: Var(α̂) — primary
    ax1.plot(xs, var_a,  color="#2ecc71", linewidth=2,   label="Var(α̂(t)) — heterogeneity")
    ax1.plot(xs, mean_a, color="#3498db", linewidth=1.5, linestyle="--", label="mean(α̂(t))")
    ax1.fill_between(xs, var_a, alpha=0.2, color="#2ecc71")
    if depeg_xs:
        ax1.axvspan(depeg_xs[0], depeg_xs[-1], alpha=0.12, color="#e74c3c", label="stETH depeg (May-Jun 2022)")
    ax1.set_ylabel("Var(α̂(t))", fontsize=10)
    ax1.legend(fontsize=9)
    ax1.set_title("α̂ = retained fraction of peak stETH holdings (revealed preference)", fontsize=10, loc="left")

    # Panel 2: Signal s(t)
    ax2.plot(xs, sig_s, color="#e74c3c", linewidth=1.5, label="s(t) = 1−stETH/ETH price ratio")
    ax2.axhline(0, color="gray", linestyle="--", linewidth=0.8)
    if depeg_xs:
        ax2.axvspan(depeg_xs[0], depeg_xs[-1], alpha=0.12, color="#e74c3c")
    ax2.set_ylabel("stETH depeg signal", fontsize=10)
    ax2.set_xlabel("Week", fontsize=10)
    ax2.legend(fontsize=9)

    # X-axis labels
    step = max(1, len(dates) // 20)
    ax2.set_xticks(xs[::step])
    ax2.set_xticklabels(dates[::step], rotation=45, ha="right", fontsize=8)

    plt.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    print(f"  Chart → {path}")

# ── Main ──────────────────────────────────────────────────────────────────────

async def main_async(args):
    if not ALCHEMY_URL:
        print("ERROR: ALCHEMY_HTTP_URL not set in .env")
        sys.exit(1)

    out_dir = Path(__file__).parent
    holders_cache = out_dir / "top_holders.json"

    start_ts = int(datetime(2021, 1, 1, tzinfo=timezone.utc).timestamp())
    end_ts   = int(datetime(2023, 7, 1, tzinfo=timezone.utc).timestamp())

    checkpoints = weekly_checkpoints(args.start, args.end)
    print(f"\n  Checkpoints: {len(checkpoints)} weeks ({args.start} → {args.end})")

    async with aiohttp.ClientSession() as session:

        # Step 1: Prices
        print("\n[1/4] Fetching stETH/ETH price series from DeFiLlama...")
        prices = await fetch_steth_prices(session, start_ts, end_ts)
        print(f"  Got {len(prices)} weekly price points")
        if prices:
            sample = list(prices.items())[:3] + list(prices.items())[-3:]
            for d, p in sample:
                depeg = f"  depeg={1-p:.4f}" if abs(1-p) > 0.001 else ""
                print(f"    {d}: stETH/ETH = {p:.6f}{depeg}")

        # Step 2: Top holders
        if args.skip_scan and holders_cache.exists():
            print(f"\n[2/4] Loading holders from cache ({holders_cache})...")
            with open(holders_cache) as f:
                top_holders = json.load(f)
        else:
            print(f"\n[2/4] Scanning Transfer events for top {args.wallets} holders...")
            # Scan around the depeg period for most relevant holders
            scan_start = ts_to_block_approx(
                int(datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp()))
            scan_end = ts_to_block_approx(
                int(datetime(2022, 8, 1, tzinfo=timezone.utc).timestamp()))
            top_holders = await scan_top_holders(
                session, args.wallets, scan_start, scan_end)
            with open(holders_cache, "w") as f:
                json.dump(top_holders, f)
            print(f"  Cached → {holders_cache}")

        print(f"  Using {len(top_holders)} wallets")

        # Step 3: Historical balances
        balances_cache = out_dir / "balances_cache.json"
        if args.skip_scan and balances_cache.exists():
            print(f"\n[3/4] Loading balances from cache ({balances_cache})...")
            with open(balances_cache) as f:
                balances = json.load(f)
        else:
            print(f"\n[3/4] Fetching weekly balances ({len(top_holders)} wallets × {len(checkpoints)} weeks)...")
            balances = await get_balances_at_blocks(session, top_holders, checkpoints)
            with open(balances_cache, "w") as f:
                json.dump(balances, f)
            print(f"  Cached → {balances_cache}")

        active = sum(1 for w, hist in balances.items() if any(v > 0.001 for v in hist.values()))
        print(f"  {active}/{len(top_holders)} wallets had non-zero balances")

    # Step 4: Compute α̂ (primary) and λ̂ where price available (secondary)
    print("\n[4/4] Computing α̂ (revealed preference) series...")
    lambda_rows, fvar_rows = compute_alpha_series(balances, prices, checkpoints)
    print(f"  {len(lambda_rows)} wallet-week observations")
    print(f"  {len(fvar_rows)} weeks with sufficient data (n≥3 wallets)")

    # Report
    print_fvar_report(fvar_rows)

    # Save
    write_csv(lambda_rows, out_dir / "lambda_estimates.csv")
    write_csv(fvar_rows,   out_dir / "f_lambda_variance.csv")

    if not args.no_plot:
        plot_fvar(fvar_rows, out_dir / "f_lambda_variance.png")

def main():
    p = argparse.ArgumentParser(description="Empirical λ estimation from on-chain stETH")
    p.add_argument("--wallets",    type=int, default=80,
                   help="Number of top holders to track (default: 80)")
    p.add_argument("--start",      default="2021-01",
                   help="Start period YYYY-MM (default: 2021-01)")
    p.add_argument("--end",        default="2023-06",
                   help="End period YYYY-MM (default: 2023-06)")
    p.add_argument("--skip-scan",  action="store_true",
                   help="Skip Transfer scan, load from top_holders.json cache")
    p.add_argument("--no-plot",    action="store_true")
    args = p.parse_args()
    asyncio.run(main_async(args))

if __name__ == "__main__":
    main()
