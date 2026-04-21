# Ethereum Foundation ESP — Grant Application
**QUEST: Macroprudential Oracle for Ethereum Consensus Layer Risk**

---

## How to Apply

**URL:** https://esp.ethereum.foundation/applicants
**Category:** Consensus Layer Tooling / Infrastructure
**Process:** Submit via ESP form → interview → decision in 3–6 weeks
**All outputs:** Open source (MIT) — already public at github.com/GuillermoSiaira/QUEST

---

## Application

### Project Name
QUEST — Macroprudential Oracle for Ethereum

### Applicant
Guillermo Siaira — guillermosiaira@gmail.com
GitHub: https://github.com/GuillermoSiaira/QUEST

---

### Problem

Ethereum's consensus layer has a structural blind spot documented in Lido's oracle
source code (`safe_border.py`): when the CL rebase is positive, the function returns
early — skipping the slashing border check entirely. This means that when MEV + consensus
rewards exceed slashing losses, the oracle signals healthy even while slashing debt
accumulates silently among remaining stakers.

This is not a Lido-specific problem. It is a systemic coordination failure: any protocol
that uses net rebase as its safety signal can be bypassed by high-MEV epochs. The Grey Zone
is an intertemporal state where apparent profitability masks technical insolvency.
Withdrawals finalize at 1:1 while real liabilities are socialized later onto remaining
stakers — without any on-chain signal that this is happening.

No permissionless, on-chain infrastructure exists today to detect and publish this risk
before it becomes a liquidation cascade.

---

### Solution

QUEST is a macroprudential oracle that computes a **Grey Zone Score** from live Beacon
chain data every epoch (~384 seconds):

```
Grey Zone Score = gross_slashing_loss / (cl_rewards + burned_eth)
```

| Score     | Risk Level | Interpretation                                      |
|-----------|------------|-----------------------------------------------------|
| < 0.5     | HEALTHY    | Normal state — losses well below rewards            |
| 0.5 – 1.0 | GREY_ZONE  | Lido oracle bypass possible — slashing debt hidden  |
| ≥ 1.0     | CRITICAL   | Losses exceed rewards including MEV                 |

The score is:
- **Computed from raw Beacon chain data** — no simulations, no models, no black boxes
- **Published on-chain** via `QUESTCore.sol` (ERC-8033 oracle interface) every epoch
- **Verifiable historically** — every epoch persisted on IPFS + Filecoin with storage proofs
- **Consumable by DeFi protocols** via `IERC8004QuestAware` — opt-in, permissionless

---

### What's Already Built

| Component                  | Status         | Details                                                     |
|----------------------------|----------------|-------------------------------------------------------------|
| Risk engine                | ✅ Production  | Python, Beacon REST API (ChainSafe Lodestar) + Alchemy      |
| Grey Zone Score            | ✅ Production  | Computing live, ~225 epochs/day since 2026-04-13            |
| FastAPI backend            | ✅ Production  | REST + WebSocket, GCP Cloud Run                             |
| AVS node (Go)              | ✅ Production  | Submits `publishGreyZoneScore` on-chain every epoch         |
| QUESTCore.sol (ERC-8033)   | ✅ Sepolia     | 0xE81C6B16ecbEC8E4Aadc963e82B27c10c4ab10e7                 |
| QUESTAwareProtocol.sol     | ✅ Sepolia     | ERC-8004 reference implementation                           |
| Live dashboard             | ✅ Public      | quest-orcin-sigma.vercel.app — real-time Grey Zone Score    |
| Epoch viewer               | ✅ Public      | /epoch/{n} — full data + JSON download                      |
| Decentralized storage      | ✅ Production  | IPFS (Pinata) + Filecoin (Lighthouse) — every epoch         |
| Foundry test suite         | ✅ Passing     | 18 tests (QUESTCore + QUESTAwareProtocol)                   |

**Live proof:** Epoch 442200 is stored at:
- IPFS: `gateway.pinata.cloud/ipfs/<CID>`
- Filecoin: `files.lighthouse.storage/viewFile/<CID>`
- Epoch viewer: `quest-orcin-sigma.vercel.app/epoch/442200`

---

### Relevance to Ethereum Foundation Priorities

1. **Consensus layer security** — QUEST directly monitors the Beacon chain for the class
   of risk that the Lido oracle bug represents. It provides independent, on-chain
   verification that no single protocol can suppress.

2. **Systemic risk transparency** — The Grey Zone Score is a public good: free, open
   source, permissionless. Any researcher, DeFi protocol, or regulator can consume it
   without trusting QUEST's infrastructure.

3. **Interoperability standard** — ERC-8033 (macroprudential oracle interface) and
   ERC-8004 (QUEST-aware protocol interface) are open standards that any protocol can
   implement. QUEST is the reference implementation.

4. **Historical verifiability** — Filecoin storage proofs make each epoch snapshot
   cryptoeconomically verifiable. This creates an immutable audit trail of Ethereum's
   systemic health — useful for post-incident analysis and regulatory compliance.

---

### Deliverables

**M1 — Mainnet deployment + historical backfill (4 weeks)**
- Deploy `QUESTCore.sol` on Ethereum mainnet
- Backfill 1,200+ existing epochs to IPFS + Filecoin
- Public API with full historical data

**M2 — Protocol-level Grey Zone Score (6 weeks)**
- Per-protocol scoring for Lido, Rocket Pool, EtherFi, Swell, Kelp
- Validator registry integration (on-chain withdrawal credentials)
- Dashboard: per-protocol risk breakdown

**M3 — ERC-8033/8004 specification + reference implementation (4 weeks)**
- Formal EIP draft for ERC-8033 (macroprudential oracle standard)
- Formal EIP draft for ERC-8004 (QUEST-aware protocol interface)
- Reference integration guide for DeFi protocols

**M4 — EigenLayer AVS decentralization (8 weeks)**
- Port trusted operator to EigenLayer AVS SDK (BLS operator set)
- 3–5 independent operators on Sepolia validating Grey Zone Score consensus
- Slashing conditions for incorrect score reporting

---

### Budget Request

| Milestone | Duration | Cost     |
|-----------|----------|----------|
| M1        | 4 weeks  | $8,000   |
| M2        | 6 weeks  | $15,000  |
| M3        | 4 weeks  | $10,000  |
| M4        | 8 weeks  | $22,000  |
| **Total** | **22 weeks** | **$55,000** |

Infrastructure costs (GCP Cloud Run, Alchemy, Pinata, Lighthouse): ~$200/month, included.

---

### Team

**Guillermo Siaira** — Full-stack engineer. Built the complete QUEST stack solo:
risk engine, API, contracts, AVS node, dashboard, storage integrations.
Background in distributed systems and DeFi protocol development.

---

### Open Source

All code is MIT licensed and public:
- Repository: https://github.com/GuillermoSiaira/QUEST
- Contracts: verified on Sepolia Etherscan
- Dashboard: live at quest-orcin-sigma.vercel.app
- API: public at quest-api-oo2ixbxsba-uc.a.run.app
