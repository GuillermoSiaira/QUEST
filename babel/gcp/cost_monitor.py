"""
Cost monitor — print estimated GCP spend for BABEL Phase 0.
Run before and after long GPU sessions to track burn rate.

Rates (us-central1, as of 2026):
  T4 GPU (n1-standard-4 + T4):  $0.35/hr
  Cloud Storage:                 $0.02/GB/month
  Egress:                        $0.08/GB
  Anthropic Claude Sonnet 4.6:  $3.00/MTok input, $15.00/MTok output
"""

import time
from datetime import datetime

T4_HOURLY = 0.35
STORAGE_MONTHLY_PER_GB = 0.02
ANTHROPIC_INPUT_PER_MTOK = 3.00
ANTHROPIC_OUTPUT_PER_MTOK = 15.00


def estimate_phase0_cost(
    gpu_hours: float = 1.0,
    storage_gb: float = 20.0,
    anthropic_input_mtok: float = 0.5,
    anthropic_output_mtok: float = 0.1,
) -> dict:
    compute = gpu_hours * T4_HOURLY
    storage = storage_gb * STORAGE_MONTHLY_PER_GB
    anthropic = (
        anthropic_input_mtok * ANTHROPIC_INPUT_PER_MTOK
        + anthropic_output_mtok * ANTHROPIC_OUTPUT_PER_MTOK
    )
    total = compute + storage + anthropic

    print(f"\n=== BABEL Phase 0 Cost Estimate ({datetime.now().strftime('%Y-%m-%d %H:%M')}) ===")
    print(f"  GPU compute  ({gpu_hours:.1f}h T4)    : ${compute:.2f}")
    print(f"  Storage      ({storage_gb:.0f}GB/month)   : ${storage:.2f}")
    print(f"  Anthropic API                   : ${anthropic:.2f}")
    print(f"  ─────────────────────────────────")
    print(f"  TOTAL PHASE 0 ESTIMATE          : ${total:.2f}")
    print(f"  Remaining budget (~$1000 total)  : ${1000 - total:.0f}")
    print()

    return {
        "compute_usd": compute,
        "storage_usd": storage,
        "anthropic_usd": anthropic,
        "total_usd": total,
    }


class GPUTimer:
    """Context manager to track GPU session duration and cost."""

    def __init__(self, label: str = "GPU session"):
        self.label = label
        self.start = None

    def __enter__(self):
        self.start = time.time()
        print(f"⏱  {self.label} started at {datetime.now().strftime('%H:%M:%S')}")
        return self

    def __exit__(self, *args):
        elapsed_hours = (time.time() - self.start) / 3600
        cost = elapsed_hours * T4_HOURLY
        print(f"⏱  {self.label} ended — {elapsed_hours*60:.1f} min — ${cost:.3f}")


if __name__ == "__main__":
    estimate_phase0_cost()
