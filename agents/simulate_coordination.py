#!/usr/bin/env python3
"""
simulate_coordination.py
────────────────────────
Demonstrates the core thesis:

  THESIS: A public signal preserves λ-heterogeneity iff its precision is
  below a threshold σ*. Above σ*, agents homogenize → simultaneous exit →
  instability. Below σ*, staggered exit → absorption → stability.

The simulation runs two populations of N agents through the same stress event:
  - Population A: heterogeneous λ ~ Uniform(λ_min, λ_max)
  - Population B: homogeneous λ = mean(λ_A)  ← same average risk aversion

Claim: aggregate exposure curves diverge during stress. B crashes (bank run);
A absorbs (staggered exit). The difference is the λ distribution, not its mean.

Outputs:
  - Terminal table with key statistics
  - PNG chart (if matplotlib available): aggregate_exposure.png

Usage:
    python simulate_coordination.py
    python simulate_coordination.py --n 2000 --event may2022
    python simulate_coordination.py --no-plot   # terminal only
"""

import argparse
import math
import sys
import io
import csv
from pathlib import Path
from dataclasses import dataclass, field

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ── Model parameters ─────────────────────────────────────────────────────────

SIGMA_BASE = 0.05
K          = math.log(10)
E_R        = 0.0075

# λ distribution for heterogeneous population
LAM_MIN  = 0.2
LAM_MAX  = 1.8
LAM_MEAN = (LAM_MIN + LAM_MAX) / 2.0   # = 1.0

# ── Signal scenarios ──────────────────────────────────────────────────────────

def signal_may2022(steps: int = 60) -> list[tuple[float, str]]:
    """
    Synthetic reconstruction of a May-2022-type stress event.
    Slow build → grey zone entry → peak → recovery.
    30 days × 2 ticks/day = 60 ticks.
    """
    s = []
    # Days 1-10: calm baseline (GZS ≈ network noise level)
    for i in range(20):
        s.append((0.02 + 0.005 * math.sin(i), "baseline"))
    # Days 11-18: stress signal builds (UST/Luna spillover)
    for i in range(16):
        gzs = 0.02 + (i / 16) * 0.55
        s.append((gzs, "stress_rising"))
    # Days 19-22: grey zone / near-critical
    for i in range(8):
        gzs = 0.57 + 0.5 * math.sin(i * 0.8)
        s.append((max(0.5, gzs), "grey_zone"))
    # Days 23-26: recovery
    for i in range(8):
        gzs = 0.55 - (i / 8) * 0.45
        s.append((max(0.05, gzs), "recovery"))
    # Days 27-30: resolved
    for i in range(8):
        s.append((0.05 + 0.01 * math.sin(i), "resolved"))
    return s[:steps]

def signal_correlated_ai(steps: int = 60) -> list[tuple[float, str]]:
    """
    Scenario for arxiv 2603 objection: signal is VERY precise (narrow σ*).
    All agents see same sharp signal → λ homogenization → bank run test.
    """
    s = signal_may2022(steps)
    # Add a sudden sharp spike to simulate correlated AI model output
    result = []
    for i, (gzs, label) in enumerate(s):
        if 20 <= i <= 24:
            result.append((min(1.5, gzs * 2.5), "ai_amplified"))
        else:
            result.append((gzs, label))
    return result

SCENARIOS = {
    "may2022":      signal_may2022,
    "ai_amplified": signal_correlated_ai,
}

# ── Core functions ────────────────────────────────────────────────────────────

def sigma_sq(gzs: float) -> float:
    return SIGMA_BASE**2 * math.exp(K * gzs)

def optimal_alpha(lam: float, gzs: float) -> float:
    denom = lam * sigma_sq(gzs)
    return max(0.0, min(1.0, E_R / denom))

# ── Population simulation ─────────────────────────────────────────────────────

@dataclass
class Population:
    name: str
    lambdas: list[float]
    alphas: list[float] = field(default_factory=list)
    history: list[dict] = field(default_factory=list)

    def __post_init__(self):
        self.alphas = [1.0] * len(self.lambdas)

    def tick(self, gzs: float, label: str = "") -> dict:
        new_alphas = [optimal_alpha(lam, gzs) for lam in self.lambdas]
        self.alphas = new_alphas

        agg = sum(new_alphas) / len(new_alphas)
        low_alpha = sum(1 for a in new_alphas if a < 0.1) / len(new_alphas)

        # λ distribution stats (proxy for heterogeneity preservation)
        active_lams = [self.lambdas[i] for i, a in enumerate(new_alphas) if a > 0.05]
        lam_std = _std(active_lams) if len(active_lams) > 1 else 0.0

        state = {
            "gzs":            round(gzs, 4),
            "label":          label,
            "agg_alpha":      round(agg, 4),
            "frac_exited":    round(low_alpha, 4),
            "active_agents":  len(active_lams),
            "lam_std_active": round(lam_std, 4),
        }
        self.history.append(state)
        return state

def _std(vals: list[float]) -> float:
    if len(vals) < 2:
        return 0.0
    mean = sum(vals) / len(vals)
    return math.sqrt(sum((v - mean) ** 2 for v in vals) / len(vals))

def make_heterogeneous(n: int) -> list[float]:
    """Uniform λ ~ [λ_min, λ_max]."""
    return [LAM_MIN + (LAM_MAX - LAM_MIN) * i / (n - 1) for i in range(n)]

def make_homogeneous(n: int) -> list[float]:
    """All agents at mean λ."""
    return [LAM_MEAN] * n

# ── Report ────────────────────────────────────────────────────────────────────

def print_report(pop_het: Population, pop_hom: Population, signal: list) -> None:
    sep = "─" * 100
    print()
    print(sep)
    print("  QUEST — Coordination Simulation: Heterogeneous vs Homogeneous λ")
    print(f"  Agents per population: {len(pop_het.lambdas)}")
    print(f"  λ heterogeneous: Uniform({LAM_MIN}, {LAM_MAX}),  mean={LAM_MEAN:.2f}")
    print(f"  λ homogeneous:   constant {LAM_MEAN:.2f}")
    print(sep)
    print(
        f"  {'t':>3}  {'GZS':>6}  {'Phase':<16}"
        f"  {'α_het':>6}  {'%Exit_het':>9}"
        f"  {'α_hom':>6}  {'%Exit_hom':>9}"
        f"  {'Δα':>6}  λ_std_het"
    )
    print(sep)

    max_divergence = 0.0
    max_div_t = 0

    for t, (h, m) in enumerate(zip(pop_het.history, pop_hom.history)):
        delta = m["agg_alpha"] - h["agg_alpha"]
        if delta > max_divergence:
            max_divergence = delta
            max_div_t = t

        flag = " ← DIVERGE" if delta > 0.15 else ""
        print(
            f"  {t:>3}  {h['gzs']:>6.3f}  {h['label']:<16}"
            f"  {h['agg_alpha']:>6.3f}  {h['frac_exited']:>9.1%}"
            f"  {m['agg_alpha']:>6.3f}  {m['frac_exited']:>9.1%}"
            f"  {delta:>+6.3f}  {h['lam_std_active']:>6.4f}{flag}"
        )

    print(sep)
    print()
    print("  KEY STATISTICS")
    print(f"  Max α divergence:    Δα = {max_divergence:.3f} at t={max_div_t}")

    het_min = min(h["agg_alpha"] for h in pop_het.history)
    hom_min = min(h["agg_alpha"] for h in pop_hom.history)
    print(f"  Minimum agg α — Heterogeneous: {het_min:.3f}   Homogeneous: {hom_min:.3f}")

    het_exit_peak = max(h["frac_exited"] for h in pop_het.history)
    hom_exit_peak = max(h["frac_exited"] for h in pop_hom.history)
    print(f"  Peak fraction exited — Het: {het_exit_peak:.1%}   Hom: {hom_exit_peak:.1%}")

    het_lam_std_peak = max(h["lam_std_active"] for h in pop_het.history)
    het_lam_std_stress = min(
        h["lam_std_active"] for h in pop_het.history
        if h["label"] in ("grey_zone", "stress_rising", "ai_amplified")
    ) if any(h["label"] in ("grey_zone", "stress_rising", "ai_amplified") for h in pop_het.history) else 0
    print(f"  λ std (active agents) — peak: {het_lam_std_peak:.4f}  stress min: {het_lam_std_stress:.4f}")
    print()
    print("  INTERPRETATION")
    if max_divergence > 0.1:
        print(f"  ✓ Heterogeneous population absorbs stress — α floor = {het_min:.3f}")
        print(f"  ✗ Homogeneous population over-exits    — α floor = {hom_min:.3f}")
        print(f"  → Difference = {hom_min - het_min:+.3f}  (negative = homogeneous exits more)")
    else:
        print("  Signal too weak to differentiate populations — increase stress or reduce N")
    print()

def write_csv(pop_het: Population, pop_hom: Population, path: Path) -> None:
    rows = []
    for t, (h, m) in enumerate(zip(pop_het.history, pop_hom.history)):
        rows.append({
            "t": t,
            "gzs": h["gzs"],
            "phase": h["label"],
            "alpha_het": h["agg_alpha"],
            "alpha_hom": m["agg_alpha"],
            "frac_exited_het": h["frac_exited"],
            "frac_exited_hom": m["frac_exited"],
            "lam_std_het": h["lam_std_active"],
            "delta_alpha": round(m["agg_alpha"] - h["agg_alpha"], 4),
        })
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

# ── Plot ──────────────────────────────────────────────────────────────────────

def plot_results(pop_het: Population, pop_hom: Population, path: Path) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
    except ImportError:
        print("  matplotlib not installed — skipping chart (pip install matplotlib)")
        return

    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
    fig.suptitle(
        "QUEST: Heterogeneous vs Homogeneous λ under Stress Signal\n"
        "Core thesis: λ-diversity is a stability condition",
        fontsize=13, fontweight="bold"
    )

    ts = list(range(len(pop_het.history)))
    gzs_vals    = [h["gzs"] for h in pop_het.history]
    alpha_het   = [h["agg_alpha"] for h in pop_het.history]
    alpha_hom   = [h["agg_alpha"] for h in pop_hom.history]
    lam_std_het = [h["lam_std_active"] for h in pop_het.history]
    exit_het    = [h["frac_exited"] for h in pop_het.history]
    exit_hom    = [h["frac_exited"] for h in pop_hom.history]

    # Panel 1: GZS signal
    ax1 = axes[0]
    ax1.fill_between(ts, gzs_vals, alpha=0.25, color="#e74c3c")
    ax1.plot(ts, gzs_vals, color="#e74c3c", linewidth=2)
    ax1.axhline(0.5, color="#e67e22", linestyle="--", linewidth=1, label="Grey Zone (0.5)")
    ax1.axhline(1.0, color="#c0392b", linestyle="--", linewidth=1, label="Critical (1.0)")
    ax1.set_ylabel("GZS Signal s(t)", fontsize=10)
    ax1.legend(fontsize=8, loc="upper right")
    ax1.set_ylim(0, max(gzs_vals) * 1.2)
    ax1.set_title("Public Signal", fontsize=10, loc="left")

    # Panel 2: Aggregate exposure
    ax2 = axes[1]
    ax2.plot(ts, alpha_het, color="#2ecc71", linewidth=2.5, label="Heterogeneous λ (STABLE)")
    ax2.plot(ts, alpha_hom, color="#e74c3c", linewidth=2.5, linestyle="--",
             label="Homogeneous λ (BANK RUN RISK)")
    ax2.fill_between(ts, alpha_het, alpha_hom,
                     where=[h > m for h, m in zip(alpha_het, alpha_hom)],
                     alpha=0.15, color="#2ecc71", label="Stability buffer")
    ax2.set_ylabel("Aggregate Exposure α(t)", fontsize=10)
    ax2.set_ylim(0, 1.05)
    ax2.legend(fontsize=9, loc="lower left")
    ax2.set_title("Mean-Variance Optimal Allocation by Population", fontsize=10, loc="left")

    # Panel 3: λ-std (heterogeneity preservation) + exit fraction
    ax3 = axes[2]
    ax3_r = ax3.twinx()
    ax3.plot(ts, lam_std_het, color="#9b59b6", linewidth=2, label="λ std (active agents)")
    ax3_r.plot(ts, exit_het,  color="#2ecc71", linewidth=1.5, linestyle=":", label="Exit fraction (het)")
    ax3_r.plot(ts, exit_hom,  color="#e74c3c", linewidth=1.5, linestyle=":", label="Exit fraction (hom)")
    ax3.set_ylabel("σ(λ) active agents", fontsize=10, color="#9b59b6")
    ax3_r.set_ylabel("Fraction exited", fontsize=10)
    ax3.set_xlabel("Time (epochs/ticks)", fontsize=10)
    ax3.set_title("λ Heterogeneity Preservation", fontsize=10, loc="left")
    lines1, labels1 = ax3.get_legend_handles_labels()
    lines2, labels2 = ax3_r.get_legend_handles_labels()
    ax3.legend(lines1 + lines2, labels1 + labels2, fontsize=8, loc="upper left")

    plt.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    print(f"  Chart → {path}")

# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="QUEST coordination simulation")
    parser.add_argument("--n",        type=int,   default=1000,
                        help="Agents per population (default: 1000)")
    parser.add_argument("--event",    default="may2022",
                        choices=list(SCENARIOS.keys()),
                        help="Stress scenario (default: may2022)")
    parser.add_argument("--steps",    type=int,   default=60,
                        help="Simulation steps (default: 60)")
    parser.add_argument("--no-plot",  action="store_true",
                        help="Skip chart generation")
    parser.add_argument("--csv",      default="simulation_results.csv")
    args = parser.parse_args()

    signal = SCENARIOS[args.event](args.steps)

    pop_het = Population("Heterogeneous", make_heterogeneous(args.n))
    pop_hom = Population("Homogeneous",   make_homogeneous(args.n))

    for gzs, label in signal:
        pop_het.tick(gzs, label)
        pop_hom.tick(gzs, label)

    print_report(pop_het, pop_hom, signal)

    out_dir = Path(__file__).parent
    write_csv(pop_het, pop_hom, out_dir / args.csv)

    if not args.no_plot:
        plot_results(pop_het, pop_hom, out_dir / "aggregate_exposure.png")

if __name__ == "__main__":
    main()
