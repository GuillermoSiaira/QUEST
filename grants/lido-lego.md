# Lido LEGO — Grant Application
**QUEST: Macroprudential Oracle for Grey Zone Slashing Risk**

---

## How to Apply

**URL:** https://lido.fi/lego
**Category:** Boulder ($10K–$100K) — significant initiative directly relevant to Lido's slashing risk
**Process:** Contact LEGO committee member via Telegram with title, authors, purpose, summary,
timeline, budget → discuss terms → proposal goes to research.lido.fi
**No centralized form** — contact is informal, direct

---

## Pitch (for initial Telegram contact)

**Title:** QUEST — Macroprudential Oracle for Lido Grey Zone Risk

**Authors:** Guillermo Siaira (guillermosiaira@gmail.com)

**Purpose:**
Build and maintain a permissionless oracle that detects the Grey Zone scenario — the specific
condition where Lido's oracle `safe_border.py` fails to activate Bunker Mode despite active
slashing: when MEV + CL rewards exceed slashing losses, the net rebase is positive, the slashing
border check is skipped, and withdrawals finalize at 1:1 while slashing debt accumulates silently.

**Summary:**

The bug is documented in Lido's own source (`src/services/safe_border.py`):

```python
if not self.is_bunker_mode:
    return ...   # early return — _get_associated_slashings_border_epoch never called
```

QUEST monitors this condition in real time with a Grey Zone Score:

```
Grey Zone Score = gross_slashing_loss / (cl_rewards + burned_eth)
```

When the score approaches 0.5–1.0 (GREY_ZONE), slashings are being masked by rewards.
When the score exceeds 1.0 (CRITICAL), losses exceed rewards even including MEV — Lido's
oracle may not activate Bunker Mode despite real insolvency conditions.

The oracle is already running in production on Ethereum mainnet, computing the score every
epoch (~6.4 minutes) since April 2026. All data is persisted on IPFS + Filecoin with
cryptoeconomic storage proofs.

**What's already built:**

| Component                | Status        |
|--------------------------|---------------|
| Risk engine (Python)     | ✅ Production  |
| Grey Zone Score (live)   | ✅ Mainnet     |
| REST + WebSocket API     | ✅ Public      |
| Live dashboard           | ✅ Public      |
| Epoch viewer + JSON      | ✅ Public      |
| IPFS + Filecoin storage  | ✅ Every epoch |
| QUESTCore.sol (ERC-8033) | ✅ Sepolia     |
| Foundry tests (18)       | ✅ Passing     |

Live: quest-orcin-sigma.vercel.app
API: quest-api-oo2ixbxsba-uc.a.run.app
Repo: github.com/GuillermoSiaira/QUEST

---

## Full Proposal (for research.lido.fi)

### Background

Lido's `safe_border.py` has a documented early return path: when `is_bunker_mode` is False,
the function returns without checking `_get_associated_slashings_border_epoch`. This means
that in high-MEV epochs, the CL rebase can be positive while meaningful slashing penalties
accumulate — and the oracle will not activate Bunker Mode.

This is not an edge case. In any epoch where MEV rewards are elevated (validator tips,
priority fees, MEV-boost payouts), the denominator of the Grey Zone Score
(`cl_rewards + burned_eth`) grows. A slashing event that would normally trigger Bunker Mode
may not do so if MEV is large enough to keep the net rebase positive.

QUEST detects this condition independently of Lido's oracle, providing:
1. An external check on Lido's safety signal
2. A public, verifiable audit trail of epochs where the Grey Zone condition was approached
3. On-chain coordination signals that Lido and other protocols can consume opt-in

### Technical Design

The Grey Zone Score is computed every epoch from:

**Numerator:** `gross_slashing_loss_eth`
- Initial penalty: `n_slashed * 1 ETH` (effective_balance / 32, consensus spec)
- Midterm penalty: proportional, using `3 * total_slashed / total_balance` (Bellatrix spec)
- Takes the maximum of both

**Denominator:** `cl_rewards_eth + burned_eth`
- `cl_rewards_eth`: delta of total validator balance between consecutive epochs, adjusted
  for new validator entries (not rewards)
- `burned_eth`: `base_fee * gas_used / 1e9` — proxy for MEV/economic activity

**Guards implemented:**
- Negative rewards discarded if magnitude exceeds `slashed_count * 32 ETH` (Beacon API noise)
- Rewards baseline preserved through API timeouts (never overwritten with 0)
- One write per epoch to Firestore (last_emitted_epoch guard)

### Deliverables

**M1 — Per-protocol Grey Zone Score for Lido (4 weeks, $12,000)**
- Identify Lido validators by withdrawal credentials (`0x01...lido_vault`)
- Compute per-protocol `gross_slashing_loss / (protocol_cl_rewards + burned_eth)`
- Dashboard: Lido-specific Grey Zone Score, separate from network-level score
- API endpoint: `/api/protocol/lido` with historical data

**M2 — Alert integration (3 weeks, $8,000)**
- Webhook notifications when Lido Grey Zone Score > 0.3 (early warning)
- Integration guide for Lido oracle team to consume QUEST signals
- Historical analysis: backfill Lido-specific score for all available epochs

**M3 — On-chain signal for Lido contracts (4 weeks, $10,000)**
- Mainnet deployment of `QUESTCore.sol`
- Lido-specific Grey Zone signal published on-chain every epoch
- `IERC8004QuestAware` integration example for Lido withdrawal contracts

**Total: $30,000 (Boulder tier)**

### Why LEGO

QUEST directly addresses a known safety gap in Lido's oracle. The system is already running
and monitoring the network — this grant funds the Lido-specific layer: per-protocol scoring,
alert integration, and on-chain signal that Lido contracts can consume.

This is not a research project. The infrastructure exists and is producing data. The grant
accelerates integration with Lido's existing systems and makes the safety signal available
to the Lido community in a consumable form.

### Contact

Guillermo Siaira
guillermosiaira@gmail.com
github.com/GuillermoSiaira/QUEST
Wallet: 0xBb3272F387dE5A2c2e3906d24EfaC460a7013f2C
