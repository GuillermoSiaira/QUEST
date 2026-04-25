#!/usr/bin/env python3
"""
quest_agent.py
──────────────
QUEST-aware autonomous agent.

An agent with a fixed risk-aversion coefficient λ that reads the public
GZS signal, computes its optimal stETH exposure α*(t), and decides whether
to rebalance. This is the minimal instantiation of the utility framework:

    U(α) = α·E(R) − (λ/2)·α²·σ²(s)
    α*(t) = max(0, E(R) / (λ·σ²(s(t))))   [first-order condition]

where σ²(s) = σ_base²·exp(k·s) scales with signal severity.

Usage:
    python quest_agent.py --lam 0.6           # single agent, default params
    python quest_agent.py --lam 1.2 --poll 60 # more risk-averse, 60s poll
    python quest_agent.py --demo              # run with synthetic signal ramp
"""

import argparse
import math
import time
import json
import sys
import io
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ── Model parameters ────────────────────────────────────────────────────────

SIGMA_BASE  = 0.05          # baseline volatility
K           = math.log(10)  # ≈ 2.303 — scaling constant
E_R         = 0.0075        # expected return per epoch (~4.5% APY / 225)
GREY_ZONE_LOWER = 0.5
GREY_ZONE_UPPER = 1.0

QUEST_API_URL = "https://quest-api-oo2ixbxsba-uc.a.run.app/latest"

# ── Core functions ────────────────────────────────────────────────────────────

def sigma_sq(gzs: float) -> float:
    """Endogenous variance: σ²(s) = σ_base²·exp(k·s)."""
    return SIGMA_BASE**2 * math.exp(K * gzs)

def optimal_alpha(lam: float, gzs: float) -> float:
    """
    α*(λ, s) = max(0, E(R) / (λ·σ²(s)))

    The fraction of portfolio that maximizes mean-variance utility.
    Falls to 0 when signal severity makes variance dominate expected return.
    """
    denom = lam * sigma_sq(gzs)
    if denom <= 0:
        return 1.0
    return max(0.0, min(1.0, E_R / denom))

def classify_gzs(gzs: float) -> str:
    if gzs >= GREY_ZONE_UPPER:
        return "CRITICAL"
    if gzs >= GREY_ZONE_LOWER:
        return "GREY_ZONE"
    return "HEALTHY"

# ── Agent class ───────────────────────────────────────────────────────────────

@dataclass
class QUESTAgent:
    """
    A single QUEST-aware agent.

    The agent has a fixed λ (risk aversion) and current exposure α_current.
    On each tick it reads the public signal, computes α*, and decides whether
    the deviation from current exposure exceeds its rebalance threshold.
    """
    lam: float                      # risk-aversion coefficient
    alpha: float = 1.0              # current exposure (starts fully invested)
    rebalance_threshold: float = 0.05  # only act if |α* − α_current| > this

    history: list = field(default_factory=list)

    def tick(self, gzs: float, timestamp: str = "") -> dict:
        alpha_star = optimal_alpha(self.lam, gzs)
        delta = alpha_star - self.alpha
        action = "HOLD"

        if abs(delta) > self.rebalance_threshold:
            direction = "REDUCE" if delta < 0 else "INCREASE"
            action = f"{direction} {abs(delta)*100:.1f}pp"
            self.alpha = alpha_star

        state = {
            "ts":         timestamp or datetime.utcnow().isoformat(),
            "gzs":        round(gzs, 4),
            "signal":     classify_gzs(gzs),
            "lam":        self.lam,
            "sigma_sq":   round(sigma_sq(gzs), 6),
            "alpha_star": round(alpha_star, 4),
            "alpha_cur":  round(self.alpha, 4),
            "action":     action,
        }
        self.history.append(state)
        return state

    def summary(self) -> dict:
        if not self.history:
            return {}
        alphas = [h["alpha_star"] for h in self.history]
        return {
            "agent_lam":    self.lam,
            "ticks":        len(self.history),
            "alpha_mean":   round(sum(alphas) / len(alphas), 4),
            "alpha_min":    round(min(alphas), 4),
            "alpha_max":    round(max(alphas), 4),
            "rebalances":   sum(1 for h in self.history if h["action"] != "HOLD"),
        }

# ── Live signal fetch ─────────────────────────────────────────────────────────

def fetch_gzs() -> tuple[float, str]:
    """Fetch current GZS from QUEST API. Returns (gzs, epoch_ts)."""
    try:
        with urllib.request.urlopen(QUEST_API_URL, timeout=5) as resp:
            data = json.loads(resp.read())
        gzs = float(data.get("grey_zone_score", data.get("gzs", 0.0)))
        ts  = data.get("timestamp", data.get("epoch_start_datetime", ""))
        return gzs, ts
    except Exception as e:
        raise RuntimeError(f"API fetch failed: {e}")

# ── Demo mode (synthetic signal) ─────────────────────────────────────────────

def demo_signal_ramp():
    """
    Synthetic signal: ramps up to GREY_ZONE, spikes to CRITICAL, recovers.
    Mimics the shape of a stress event (e.g. May 2022 analog).
    """
    import itertools
    # (gzs, label)
    sequence = (
        [(0.02, "baseline")] * 5
        + [(0.1 * i, "stress_rising") for i in range(1, 7)]
        + [(0.6, "grey_zone_entry")] * 3
        + [(1.1, "critical_peak")] * 2
        + [(0.8, "post_peak")] * 2
        + [(0.4, "recovery")] * 3
        + [(0.1, "resolved")] * 5
    )
    return iter(sequence)

# ── CLI ───────────────────────────────────────────────────────────────────────

def _fmt_row(state: dict) -> str:
    bar_len = int(state["alpha_star"] * 20)
    bar = "█" * bar_len + "░" * (20 - bar_len)
    return (
        f"  [{state['ts'][-8:] if len(state['ts']) > 8 else state['ts']:>8}]"
        f"  GZS={state['gzs']:.4f}  {state['signal']:<10}"
        f"  λ={state['lam']:.2f}"
        f"  α*={state['alpha_star']:.3f}  [{bar}]"
        f"  {state['action']}"
    )

def main():
    parser = argparse.ArgumentParser(description="QUEST-aware autonomous agent")
    parser.add_argument("--lam",   type=float, default=0.6,
                        help="Risk-aversion coefficient λ (default: 0.6)")
    parser.add_argument("--poll",  type=int,   default=30,
                        help="Poll interval in seconds (default: 30)")
    parser.add_argument("--ticks", type=int,   default=0,
                        help="Stop after N ticks (0 = run forever)")
    parser.add_argument("--demo",  action="store_true",
                        help="Run with synthetic stress signal instead of live API")
    args = parser.parse_args()

    agent = QUESTAgent(lam=args.lam)

    print()
    print("━" * 80)
    print(f"  QUEST Agent  |  λ={args.lam}  |  mode={'DEMO' if args.demo else 'LIVE'}")
    print(f"  α*(λ, s=0) = {optimal_alpha(args.lam, 0.0):.3f}  (fully healthy baseline)")
    print(f"  α*(λ, s=0.5) = {optimal_alpha(args.lam, 0.5):.3f}  (grey zone entry)")
    print(f"  α*(λ, s=1.0) = {optimal_alpha(args.lam, 1.0):.3f}  (critical)")
    print("━" * 80)
    print()

    signal_source = demo_signal_ramp() if args.demo else None
    tick = 0

    try:
        while True:
            if args.demo:
                item = next(signal_source, None)
                if item is None:
                    break
                gzs, label = item
                ts = f"t={tick:03d}({label})"
            else:
                gzs, ts = fetch_gzs()

            state = agent.tick(gzs, ts)
            print(_fmt_row(state))

            tick += 1
            if args.ticks and tick >= args.ticks:
                break
            if not args.demo:
                time.sleep(args.poll)

    except KeyboardInterrupt:
        pass

    print()
    print("  Summary:", json.dumps(agent.summary(), indent=2))
    print()

if __name__ == "__main__":
    main()
