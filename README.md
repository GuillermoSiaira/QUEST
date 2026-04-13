# QUEST — EVM Solvency Monitor

> Macroprudential oracle for the Ethereum ecosystem. Detects **Grey Zone** risk in LRT protocols in real time.

## What is QUEST?
QUEST exists because a subtle bug in the Lido Oracle can mask insolvency risk. The oracle's `safe_border.py` can return early based on a positive rebase, skipping the slashings check; when MEV and consensus rewards outweigh slashing losses, the protocol appears healthy even as slashing debt accumulates in the background.

This creates a **Grey Zone**: an intertemporal state where apparent profitability hides technical insolvency. In practice, withdrawals can finalize at 1:1 while real slashing liabilities are socialized later across remaining stakers.

QUEST monitors that Grey Zone in real time. It computes gross slashing exposure, compares it to rewards (CL + MEV), and emits a macroprudential signal that can be consumed by protocols, dashboards, and autonomous agents.

## Grey Zone Score
Grey Zone Score = `gross_slashing_loss / (cl_rewards + mev_rewards)`

Thresholds:
- **HEALTHY** if score < 0.5
- **GREY_ZONE** if 0.5 <= score < 1.0
- **CRITICAL** if score >= 1.0

## Architecture
```
Ethereum Beacon REST API (ChainSafe Lodestar) + Alchemy
  -> risk-engine/data_pipeline.py   (ingesta + EpochSnapshot)
  -> risk-engine/lrt_risk_model.py  (Grey Zone Score)
  -> risk-engine/grpc_server.py     (gRPC — SystemicRiskOracle)
  -> FastAPI (Cloud Run)            (REST + WebSocket)
  -> Next.js Dashboard (Vercel)
```

## Stack
- **Backend:** Python 3.11, FastAPI, aiohttp, web3.py, aiosqlite, grpcio
- **Frontend:** Next.js 16, TypeScript, Tailwind CSS, Recharts
- **Infrastructure:** GCP Cloud Run, GCP Secret Manager, Vercel
- **Data sources:** Ethereum Beacon REST API — lodestar-mainnet.chainsafe.io (Consensus Layer), Alchemy (Execution Layer)
- **gRPC service:** `risk-engine/quest.proto` — `SystemicRiskOracle.CalculateGreyZoneScore`

## Local Development
```
# Clone the repo
# git clone <repo-url>
# cd QUEST

cp .env.example .env

# Backend
cd api
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8080

# Frontend
cd ../dashboard
npm install
npm run dev
```

## Deploy
- Backend: `bash deploy.sh`
- Frontend: deploy `dashboard/` with Vercel

## Monitored Protocols
| Protocol | Token | Status |
|---|---|---|
| Lido | stETH | Supported |
| Rocket Pool | rETH | Supported |
| EtherFi | eETH | Supported |
| Swell | swETH | Supported |
| Kelp | rsETH | Supported |

## License
MIT
