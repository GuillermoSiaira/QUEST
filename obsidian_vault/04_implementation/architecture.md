---
tags: [implementation, architecture, stack]
tipo: referencia
estado: produccion
---

# Arquitectura QUEST

Stack completo de producción. Tres capas: cómputo off-chain → API pública → contratos on-chain.

---

## Diagrama

```
Ethereum Mainnet (Beacon + Execution Layer)
        ↓
risk-engine (Python / aiohttp) — polling cada epoch
        ├─ Beacon REST: slashings, validator_balances, participation
        └─ Alchemy JSON-RPC: EIP-1559 burn, gas, Lido TVL
        ↓
EpochSnapshot → Grey Zone Score (lrt_risk_model.py)
        ├─ FastAPI (GCP Cloud Run) — REST público + WebSocket
        ├─ Firestore (hot storage, <100ms reads)
        ├─ IPFS / Pinata (content-addressed, CIDv1)
        └─ Filecoin / Lighthouse (storage proofs verificables)
        ↓
AVS Node (Go) — publica on-chain cada ~384s
        └─ QUESTCore.sol en Sepolia
```

---

## Servicios en producción (GCP Cloud Run)

| Servicio | URL | Estado |
|----------|-----|--------|
| `quest-api` | `quest-api-oo2ixbxsba-uc.a.run.app` | ✅ Live |
| `quest-risk-engine` | privado (gRPC) | ✅ Live |
| `quest-avs-node` | privado | ✅ Live |

**Dashboard**: `quest-orcin-sigma.vercel.app`

---

## Módulos clave

| Módulo | Descripción |
|--------|-------------|
| `risk-engine/data_pipeline.py` | Ingesta Beacon REST + Alchemy → EpochSnapshot |
| `risk-engine/lrt_risk_model.py` | [[grey_zone_score\|Grey Zone Score]] desde EpochSnapshot |
| `risk-engine/consensus_constants.py` | Constantes del consensus spec de Ethereum |
| `api/main.py` | FastAPI: REST + WebSocket + pipeline callbacks |
| `api/ipfs_store.py` | Pinata V3 (IPFS) + Lighthouse (Filecoin) |

---

## Persistencia descentralizada (3 capas)

| Capa | Proveedor | Campo | Estado |
|------|-----------|-------|--------|
| Hot | GCP Firestore | — | ✅ Live |
| IPFS | Pinata V3 | `ipfs_cid` | ✅ Live desde 2026-04-19 |
| Filecoin | Lighthouse | `filecoin_cid` | ✅ Live desde 2026-04-19 |

Cada epoch: `asyncio.gather(_pin_ipfs(), _pin_filecoin())` — paralelo, ~2s vs ~4s secuencial.

---

## Limitación técnica activa

`validator_balances` query: 2.25M registros, ~15 MB de respuesta, ~130 segundos en PublicNode. Esto produce `rewards=n/a` frecuentemente. La solución arquitectural (fórmula de issuance del consensus spec en lugar del query) está diseñada pero no implementada.

→ Ver contratos: [[contracts]]
→ Ver señal PMC 5D: [[pmc_signal]]
