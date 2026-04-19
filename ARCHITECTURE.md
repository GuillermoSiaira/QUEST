# QUEST — Architecture & Technical Decisions

> Este documento registra las decisiones arquitectónicas tomadas y su justificación.
> No reabrir decisiones marcadas como [FINAL] sin consenso explícito.

---

## Decisiones de Arquitectura

### [FINAL] AVS sobre EIP directo
Construir QUEST como AVS en EigenLayer en lugar de pugnar por aprobación de ERC-8033
como EIP oficial. Razón: el proceso de aprobación de EIPs puede tomar años. EigenLayer
permite lanzar el servicio de oráculo macroprudencial de forma rápida y descentralizada,
con seguridad garantizada por restaking económico.

### [FINAL] Go + gRPC + Python puro (sin dependencias de simulación cuántica)
El AVS node (EigenLayer) opera en Go. El risk-engine es Python nativo con cálculo
aritmético puro (sin Qiskit). La solución es una arquitectura de microservicios: Go
actúa como "comunicador" que recibe requests de la red EigenLayer, llama al servidor
gRPC Python, recibe el GreyZoneScore calculado, lo firma criptográficamente y lo
publica on-chain.
Referencia: patrón Go↔gRPC↔backend del MEV Engineering Stack (Faraone-Dev).
Nota: optimización cuadrática (Qiskit) reservada como línea de investigación futura,
no como dependencia de producción.

### [FINAL] Permissionless por diseño
QUEST no pausa transacciones ni coerciona agentes. Solo emite señales (θ, QSR).
Los agentes optan por reaccionar a θ a cambio de mejor reputación ERC-8004.
Esto es crítico para la legitimidad del proyecto como public good.

### [FINAL] Branding cuántico acotado al whitepaper
En código y contratos: "Quadratic Solvency Optimization", "Computational Stress Testing".
En whitepaper y manifesto: "Hamiltoniano", "Topología de la verdad", "Ventaja Cuántica".
Razón: evitar que desarrolladores desestimen el proyecto como narrativa de marketing.

### [FINAL] Holesky como testnet (no Sepolia)
EigenLayer tiene sus contratos desplegados en Holesky. Sepolia no tiene ServiceManager
de EigenLayer. Flujo: Local (DevKit) → Holesky → Mainnet.

### [FINAL] Off-chain computation obligatorio
El cálculo del GreyZoneScore no puede correr en la EVM (lectura de APIs externas,
aritmética de punto flotante). La capa de cómputo siempre será off-chain.
A futuro: certificada por staking económico de operadores AVS (EigenLayer).

### [FINAL] Scope: Ethereum L1 únicamente (v1)
QUEST monitorea la brecha entre tiempo de bloque y finalidad de epoch en Ethereum L1.
L2s (Arbitrum, Optimism, Base) son expansión natural para v2, no scope actual.

---

## Stack Tecnológico

### Data Sources
| Layer | Provider | Endpoint | Datos |
|---|---|---|---|
| Execution | Alchemy (Mainnet) | HTTPS + WebSocket | TVL Lido, gas price, burned ETH proxy |
| Consensus | Beacon REST API (ChainSafe Lodestar) | REST | Slashings, rewards, epoch state, validator status, participation |

### Compute Layer (risk-engine/)
- **Lenguaje:** Python 3.11+
- **Cálculo de riesgo:** Python puro (aritmética del consensus spec, sin dependencias de simulación)
- **Bridge:** gRPC server (grpcio)
- **Archivos clave:**
  - `data_pipeline.py` — ingesta Alchemy + Beaconcha.in
  - `lrt_risk_model.py` — modelo de riesgo cuadrático
  - `qsr_calculator.py` — cálculo del Quantum Solvency Ratio
  - `grpc_server.py` — servidor gRPC para comunicación con Go

### AVS Node (quest-avs-node/)
- **Lenguaje:** Go
- **Framework:** EigenLayer DevKit (avs create)
- **Responsabilidad:** Recibir task requests, llamar gRPC Python, firmar resultado, publicar on-chain
- **Archivos clave:**
  - `main.go` — entry point del nodo AVS
  - `task_handler.go` — lógica de procesamiento de tasks
  - `grpc_client.go` — cliente gRPC hacia Python

### Contracts (contracts/)
- **Framework:** Foundry
- **Red actual:** Local (Anvil) → Holesky → Mainnet
- **Contratos clave:**
  - `QUESTCore.sol` — contrato principal: almacena θ, QSR, métricas D_k
  - `interfaces/IERC8033.sol` — estándar del oráculo macroprudencial
  - `interfaces/IERC8004QuestAware.sol` — interfaz para agentes que reaccionan a θ

### Dashboard (dashboard/)
- **Framework:** Next.js 16 + React (App Router, Turbopack)
- **Deploy:** Vercel (auto-deploy desde master) → quest-orcin-sigma.vercel.app
- **Datos:** WebSocket (`/ws/feed`) para live feed; REST (`/api/status`, `/api/history`) para carga inicial
- **Componentes clave:**
  - `EpochHeader.tsx` — stat bar con acento de color por risk level
  - `StorageProof.tsx` — barra de persistencia 3 capas (Firestore · IPFS · Filecoin) con dots de estado
  - `TimelineCharts.tsx` — gráficos de Grey Zone Score, Participation Rate, Slashed Validators (50 epochs)
  - `EpochInterpretation.tsx` — análisis en lenguaje natural via Claude API
  - `app/epoch/[epoch]/page.tsx` — epoch viewer con Download JSON funcional y proof de storage
- **Público:** Todos — desarrolladores, operadores, auditores, grant reviewers

---

## Flujo de Datos (End-to-End)

```
Ethereum Mainnet
    │
    ├── Execution Layer (Alchemy)
    │   └── Gas price, burned ETH, Lido TVL
    │
    └── Consensus Layer (Beacon REST API)
        └── Epoch state, slashings, rewards, participation
                │
                ▼
        data_pipeline.py (Python) — poll cada 60s, emite 1 snapshot/epoch
        → EpochSnapshot: balance delta → epoch_rewards_gwei
        → Guard: rewards < 0 con 0 slashings → discard (Beacon API timing noise)
                │
                ▼
        lrt_risk_model.py (Python puro)
        → Grey Zone Score = gross_slashing_loss / (cl_rewards + burned_eth)
        → RiskAssessment: HEALTHY / GREY_ZONE / CRITICAL
                │
                ▼
        on_new_snapshot() — main.py (asyncio)
        → save_epoch() → Firestore
        → asyncio.gather:
            ├── pin_epoch()      → Pinata V3 → IPFS CID (CIDv1, gateway.pinata.cloud)
            └── store_filecoin() → Lighthouse → Filecoin CID (files.lighthouse.storage)
        → update_epoch_cid() + update_epoch_filecoin() → Firestore
        → model_copy(ipfs_cid, filecoin_cid) → broadcast WebSocket
                │
         ┌──────┴──────────┐
         ▼                  ▼
    Go AVS Node         Dashboard (Next.js)
    → QUESTCore.sol     → EpochHeader + StorageProof
    → on-chain every    → /epoch/[n] viewer
      ~384s             → Download JSON button
```

### Persistencia de cada epoch
| Capa | Proveedor | Acceso | Latencia |
|---|---|---|---|
| Hot | Firestore (`epoch_snapshots`) | API interna | < 100ms |
| IPFS | Pinata V3 (`network=public`) | `gateway.pinata.cloud/ipfs/<CID>` | ~1-2s upload |
| Filecoin | Lighthouse (`/api/v0/add`) | `files.lighthouse.storage/viewFile/<CID>` | ~5-30s upload |

**Nota sobre CIDs en el JSON almacenado:** Los campos `ipfs_cid` y `filecoin_cid` aparecen como `null`
en el JSON guardado en IPFS/Filecoin — esto es correcto (referencia circular: el CID no puede
contenerse a sí mismo). Los CIDs se guardan solo en Firestore y se sirven vía la API.

---

## Estado de Fases (actualizado 2026-04-19)

| Fase | Estado |
|---|---|
| Fase 1 — Risk Engine (data pipeline + Grey Zone Score + gRPC) | ✅ COMPLETADA |
| Fase 2 — Contratos (QUESTCore + QUESTAwareProtocol en Sepolia) | ✅ COMPLETADA |
| Fase 3 — AVS Node (Go, Cloud Run, on-chain cada epoch) | ✅ COMPLETADA |
| Fase 3.5 — Storage descentralizado (IPFS + Filecoin + epoch viewer) | ✅ COMPLETADA |
| Fase 4 — Grants (EigenLayer, Filecoin, EF ESP, Lido) | 🔄 En curso |
| Fase 5 — Descentralización completa (on-chain CIDs, backfill, MEV) | ⏳ Pendiente |
| Fase 6 — Cobertura multi-protocolo (Lido, Rocket Pool, EtherFi, Swell, Kelp) | ⏳ Pendiente |

## Próximos Pasos

### Fase 5 — Descentralización completa
- [ ] Publicar `filecoin_cid` on-chain en `QUESTCore.sol` cada epoch
- [ ] Script de backfill histórico: 1,243+ epochs a IPFS + Filecoin
- [ ] MEV-Boost data feed: reemplazar proxy `burned_eth` con datos reales de Flashbots
- [ ] Migrar AVS node de GCP a Pinata OpenClaw Agents

### Fase 6 — Cobertura multi-protocolo
Desagregar el riesgo de red por protocolo LST/LRT. Hoy QUEST monitorea Ethereum en su totalidad;
Fase 6 añade scores individuales por protocolo.

| Protocolo | Token | Fuente TVL | Estado |
|---|---|---|---|
| Lido | stETH | `stETH.totalSupply()` (ya integrado) | ✅ Parcial |
| Rocket Pool | rETH | `rETH.totalSupply()` × precio | ⏳ Pendiente |
| EtherFi | eETH | `EETH.totalValueOutOfLp()` | ⏳ Pendiente |
| Swell | swETH | `swETH.totalSupply()` × precio | ⏳ Pendiente |
| Kelp | rsETH | `LRTDepositPool.getTotalAssetDeposits()` | ⏳ Pendiente |

Además: filtrado de slashings por withdrawal credentials → `grey_zone_{protocolo}` individual.
