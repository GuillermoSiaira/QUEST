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

### [FINAL] Go + gRPC + Python (no reescribir Qiskit en Go)
El AVS node (EigenLayer) opera en Go. El motor cuántico (Qiskit) es Python nativo.
La solución es una arquitectura de microservicios: Go actúa como "comunicador" que
recibe requests de la red EigenLayer, llama al servidor gRPC Python, recibe el QSR
calculado, lo firma criptográficamente y lo publica on-chain.
Referencia: patrón Go↔gRPC↔backend pesado del MEV Engineering Stack (Faraone-Dev).

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
Qiskit no puede correr en la EVM. La capa de cómputo siempre será off-chain.
A futuro: certificada por staking económico de operadores AVS (EigenLayer).

### [FINAL] Scope: Ethereum L1 únicamente (v1)
QUEST monitorea la brecha entre tiempo de bloque y finalidad de epoch en Ethereum L1.
L2s (Arbitrum, Optimism, Base) son expansión natural para v2, no scope actual.

---

## Stack Tecnológico

### Data Sources
| Layer | Provider | Endpoint | Datos |
|---|---|---|---|
| Execution | Alchemy (Mainnet) | HTTPS + WebSocket | TVL, reservas, withdrawals, gas, eventos |
| Consensus | Beaconcha.in | REST API | Slashings, rewards, epoch state, validator status |

### Compute Layer (quantum-engine/)
- **Lenguaje:** Python 3.11+
- **Motor cuántico:** Qiskit (optimización cuadrática, Hamiltoniano de Ising)
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
- **Framework:** Next.js + React
- **Datos:** WebSocket desde data_pipeline.py
- **Métricas:** Prometheus + Grafana (infraestructura), UI custom (público)
- **Público:** Todos — desarrolladores, operadores, público general

---

## Flujo de Datos (End-to-End)

```
Ethereum Mainnet
    │
    ├── Execution Layer (Alchemy WebSocket)
    │   └── Bloques nuevos, eventos, gas, MEV proxy
    │
    └── Consensus Layer (Beaconcha.in API)
        └── Epochs, slashings, rewards por validador
                │
                ▼
        data_pipeline.py (Python)
        → Normaliza y combina datos
        → Calcula D_k (Epoch Temporal Density)
                │
                ▼
        qsr_calculator.py (Python + Qiskit)
        → Mapea estado a Hamiltoniano de Ising
        → Resuelve optimización cuadrática
        → Emite QSR + señal θ
                │
         ┌──────┴──────┐
         ▼             ▼
    gRPC server    WebSocket
    (Go AVS)       (Dashboard)
         │
         ▼
    QUESTCore.sol
    → Almacena θ on-chain
    → Agentes ERC-8004 reaccionan
```

---

## Próximos Pasos

### Fase 1 — Data Pipeline (Ahora)
- [ ] `data_pipeline.py`: conectar Alchemy + Beaconcha.in
- [ ] Validar datos reales de slashings y rewards por epoch
- [ ] `qsr_calculator.py`: adaptar `quantum_exploit.py` como módulo limpio

### Fase 2 — Contratos Base (Holesky)
- [ ] Refactorizar `QUESTCore.sol`
- [ ] Implementar `IERC8004QuestAware`
- [ ] Desplegar en Holesky con Foundry

### Fase 3 — Dashboard Público
- [ ] UI en tiempo real con datos reales
- [ ] Publicar como public good

### Fase 4 — AVS (EigenLayer)
- [ ] `avs create` con DevKit
- [ ] Bridge Go↔Python via gRPC
- [ ] Desplegar en Holesky EigenLayer

### Fase 5 — Grants
- [ ] Ethereum Foundation
- [ ] EigenLayer Foundation
- [ ] Lido Grants Program
