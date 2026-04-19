# QUEST — Macroprudential Oracle AVS for Ethereum

> A permissionless, on-chain risk coordination layer for the Ethereum consensus layer.
> Detects **Grey Zone** systemic risk in real time and publishes macroprudential signals every epoch (~384s).

**Live dashboard:** [quest-orcin-sigma.vercel.app](https://quest-orcin-sigma.vercel.app)  
**Public API:** [quest-api-oo2ixbxsba-uc.a.run.app](https://quest-api-oo2ixbxsba-uc.a.run.app)

---

## The Problem

Ethereum's consensus layer has a structural blind spot. Lido's oracle `safe_border.py` returns early when the CL rebase is positive — skipping the slashing check. When MEV + consensus rewards outweigh slashing losses, the protocol appears healthy even as slashing debt accumulates silently among remaining stakers.

This is the **Grey Zone**: an intertemporal state where apparent profitability hides technical insolvency. Withdrawals can finalize at 1:1 while real liabilities are socialized later. No on-chain coordination layer exists to signal this before it becomes a liquidation cascade.

QUEST is the equivalent of a Bank for International Settlements (BIS) for Ethereum — a permissionless macroprudential oracle that monitors this risk and emits coordination signals that DeFi protocols can consume opt-in.

---

## Grey Zone Score

```
Grey Zone Score = gross_slashing_loss / (cl_rewards + burned_eth)
```

| Score | Risk Level |
|---|---|
| < 0.5 | HEALTHY |
| 0.5 – 1.0 | GREY_ZONE |
| ≥ 1.0 | CRITICAL |

Computed from live Beacon chain data every epoch using Python arithmetic — no simulations, no black boxes. Published on-chain via `QUESTCore.sol` and certified by the AVS operator set.

---

## What's Already Built

| Component | Status | Details |
|---|---|---|
| Risk engine | ✅ Production | Python, Beacon REST + Alchemy, Cloud Run |
| FastAPI backend | ✅ Production | REST + WebSocket, 200 epochs in memory |
| AVS node (Go) | ✅ Production | Submits `reportEpochMetrics` + `publishGreyZoneScore` on-chain every epoch |
| QUESTCore.sol | ✅ Sepolia | [0xE81C6B16ecbEC8E4Aadc963e82B27c10c4ab10e7](https://sepolia.etherscan.io/address/0xE81C6B16ecbEC8E4Aadc963e82B27c10c4ab10e7) |
| QUESTAwareProtocol.sol | ✅ Sepolia | [0xD693C783AbDCe3B53b2C33D8fEB0ff4E70f12735](https://sepolia.etherscan.io/address/0xD693C783AbDCe3B53b2C33D8fEB0ff4E70f12735) |
| Live dashboard | ✅ Public | [quest-orcin-sigma.vercel.app](https://quest-orcin-sigma.vercel.app) |
| Decentralized storage | ✅ Production | IPFS (Pinata) + Filecoin (Lighthouse) — every epoch |
| Epoch viewer | ✅ Public | `/epoch/{n}` — full data + download JSON |

Every epoch snapshot is persisted across three independent layers simultaneously:
- **Firestore** — hot storage, sub-100ms reads
- **IPFS** — content-addressed via Pinata (`gateway.pinata.cloud/ipfs/<CID>`)
- **Filecoin** — storage proof via Lighthouse (`files.lighthouse.storage/viewFile/<CID>`)

---

## Architecture

```
Ethereum Mainnet
  ├── Consensus Layer (Beacon REST API — ChainSafe Lodestar)
  │     slashings, rewards, participation, validator state
  └── Execution Layer (Alchemy)
        gas price, burned ETH, Lido TVL

          ↓
  risk-engine/data_pipeline.py   — EpochSnapshot every ~384s
  risk-engine/lrt_risk_model.py  — Grey Zone Score
          ↓
  api/main.py (FastAPI, Cloud Run)
  → Firestore (hot)
  → IPFS via Pinata (content-addressed)       } parallel
  → Filecoin via Lighthouse (storage proof)   }
  → WebSocket broadcast to dashboard
  → REST: /api/status · /api/history · /api/epoch/{n}
          ↓
  ┌─────────────────┬──────────────────┐
  │  Dashboard       │  AVS Node (Go)   │
  │  Next.js/Vercel  │  Cloud Run       │
  │  live metrics    │  → QUESTCore.sol │
  │  epoch viewer    │  → Sepolia every │
  │  storage proof   │    ~384s         │
  └─────────────────┴──────────────────┘
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Healthcheck + snapshot count |
| GET | `/api/status` | Latest EpochStatus |
| GET | `/api/history?n=50` | Last n snapshots (max 200) |
| GET | `/api/epoch/{n}` | Specific epoch by number |
| WS  | `/ws/feed` | Real-time stream (FeedMessage JSON) |

Example:
```bash
curl https://quest-api-oo2ixbxsba-uc.a.run.app/api/status
curl https://quest-api-oo2ixbxsba-uc.a.run.app/api/epoch/442200
```

---

## Smart Contracts

### `QUESTCore.sol` — ERC-8033 Oracle
Stores Grey Zone Score, epoch metrics, and PMC signal (θ) on-chain.
- `reportEpochMetrics(epoch, validators, balance, participation, rewards, slashed)` — callable by registered operators
- `publishGreyZoneScore(epoch, score, riskLevel, signal)` — publishes θ signal
- `updateAgentReputation(agent, score)` — ERC-8004 reputation tracking

### `QUESTAwareProtocol.sol` — ERC-8004 Reference Implementation
Reference DeFi protocol that consumes QUEST signals and adjusts defensively.
- `setRiskThreshold(threshold)` — configure when to activate conservative mode
- `executeProtectedAction()` — reverts if Grey Zone Score exceeds threshold

### Interfaces
- `IERC8033` — macroprudential oracle standard
- `IERC8004QuestAware` — interface for QUEST-aware protocols

---

## Stack

| Layer | Technology |
|---|---|
| Risk engine | Python 3.11, aiohttp, web3.py, grpcio |
| API | FastAPI, uvicorn, google-cloud-firestore |
| AVS node | Go, EigenLayer SDK (trusted operator v1) |
| Contracts | Solidity 0.8.24, Foundry |
| Dashboard | Next.js 16, TypeScript, Tailwind CSS, Recharts |
| Storage | GCP Firestore, IPFS/Pinata, Filecoin/Lighthouse |
| Infrastructure | GCP Cloud Run, GCP Secret Manager, Vercel |

---

## Roadmap

| Phase | Status |
|---|---|
| Phase 1 — Risk engine + Grey Zone Score | ✅ Complete |
| Phase 2 — On-chain contracts (Sepolia) | ✅ Complete |
| Phase 3 — AVS node (trusted operator) | ✅ Complete |
| Phase 3.5 — Decentralized storage (IPFS + Filecoin) | ✅ Complete |
| Phase 4 — Grants (EigenLayer, Filecoin, EF ESP) | 🔄 In progress |
| Phase 5 — EigenLayer AVS (BLS operators, mainnet) | ⏳ Pending funding |

---

## Local Development

```bash
git clone https://github.com/GuillermoSiaira/QUEST.git
cd QUEST
cp .env.example .env  # add BEACON_API_KEY, ALCHEMY_KEY, PINATA_JWT, LIGHTHOUSE_API_KEY

# Backend
cd api
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8080

# Frontend
cd ../dashboard
npm install
npm run dev
```

---

## License

MIT
