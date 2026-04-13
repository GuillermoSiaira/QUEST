# QUEST: Quantum Economic Stress Testing
**Sovereign Stability Agent & Macroprudential Oracle for the EVM**

> **Instrucción para Claude Code:** Este archivo es el contexto principal del proyecto QUEST.
> Léelo completo antes de tocar cualquier archivo del repo. No preguntes por contexto que ya esté aquí.

---

## ¿Qué es QUEST en una oración?

QUEST es un agente autónomo supraprotocolar y *permissionless* que actúa como el equivalente
a un "BIS" (Banco de Pagos Internacionales) on-chain para Ethereum — monitorea riesgo sistémico
intertemporal (la brecha entre validación del bloque y finalidad del epoch) y coordina la
economía de agentes mediante señales macroprudenciales.

---

## Tesis Fundacional: El Bug de Lido que justifica QUEST

**Fuente:** `_LIDO_ORACLE_BUG_BOUNTY_REPORT_DRAFT.pdf` y `quantum_exploit.py`

El oracle de Lido determina si activar "Bunker Mode" verificando si el CL rebase es negativo.
Si MEV/rewards > slashings → rebase positivo → `is_bunker = False` → `safe_border.py` retorna
`_get_default_requests_border_epoch()` sin verificar slashings incompletos.

**Resultado:** Retiros se finalizan a 1:1 mientras deuda de slashing se socializa entre
los stakers restantes. Este es el **Riesgo Moral Algorítmico**: protocolos individuales
optimizan su máximo local (liquidez/velocidad) dejando zonas grises de insolvencia técnica.

**Fix sugerido en el report:** Desacoplar el chequeo de slashings del estado de Bunker Mode.
Siempre calcular `associated_slashings_border_epoch`, independientemente de `is_bunker`.

Esta vulnerabilidad demuestra empíricamente por qué un agente macroprudencial externo (QUEST)
es indispensable — los protocolos no se auto-regularán en detrimento de su UX.

---

## Estado Actual del Repositorio

### Código en producción (GCP Cloud Run):
| Servicio | URL | Estado |
|---|---|---|
| `quest-api` | https://quest-api-299259685359.us-central1.run.app | ✅ Running |
| `quest-risk-engine` | https://quest-risk-engine-299259685359.us-central1.run.app | ✅ Running (gRPC, privado) |
| `quest-avs-node` | https://quest-avs-node-299259685359.us-central1.run.app | ✅ Running (privado) |

### Contratos desplegados:
| Contrato | Red | Address | Tx |
|---|---|---|---|
| `QUESTCore` | Sepolia | `0xE81C6B16ecbEC8E4Aadc963e82B27c10c4ab10e7` | `0x48ebe0a7...e8ded2` |
| `QUESTAwareProtocol` | Sepolia | `0xD693C783AbDCe3B53b2C33D8fEB0ff4E70f12735` | verified ✅ |

Operator: `0xBb3272F387dE5A2c2e3906d24EfaC460a7013f2C`

### Persistencia:
- **Firestore** (GCP `quest-493015`, colección `epoch_snapshots`, free tier)
- Persistente entre reinicios y redeploys — historial acumulativo
- Service account: `299259685359-compute@developer.gserviceaccount.com` con `roles/datastore.user`

### Módulos del risk-engine:
| Archivo | Descripción |
|---|---|
| `risk-engine/data_pipeline.py` | Ingesta Beacon REST API + Alchemy → EpochSnapshot |
| `risk-engine/lrt_risk_model.py` | Grey Zone Score desde EpochSnapshot (Python puro) |
| `risk-engine/consensus_constants.py` | Constantes del consensus spec de Ethereum |
| `risk-engine/grpc_server.py` | Servidor gRPC: SystemicRiskOracle.CalculateGreyZoneScore |
| `risk-engine/quest.proto` | Contrato gRPC (proto3) |
| `test/TheSmartExit.t.sol` | PoC en Solidity (Foundry): demuestra el vector de arbitraje en Lido |

### Contratos (Fase 2 — en progreso):
| Archivo | Descripción |
|---|---|
| `contracts/QUESTCore.sol` | Contrato principal: reportEpochMetrics, publishGreyZoneScore, updateAgentReputation |
| `contracts/QUESTAwareProtocol.sol` | Implementación de referencia ERC-8004: protocolo DeFi que consume señales QUEST |
| `contracts/interfaces/IERC8033.sol` | Interfaz del oráculo macroprudencial |
| `contracts/interfaces/IERC8004QuestAware.sol` | Interfaz para protocolos QUEST-aware |
| `test/QUESTCore.t.sol` | Tests Foundry (10 casos) |
| `test/QUESTAwareProtocol.t.sol` | Tests Foundry (8 casos) |
| `script/Deploy.s.sol` | Deploy script para QUESTCore |
| `script/DeployQUESTAwareProtocol.s.sol` | Deploy script para QUESTAwareProtocol |
| `foundry.toml` | Config Foundry (Sepolia + Mainnet fork) |
| `contracts/SPEC.md` | Especificación de contratos (referencia) |

### Entornos configurados:
- **Python:** dependencias en `risk-engine/requirements.txt` (sin Qiskit en producción)
- **Foundry:** Configurado con fork de Mainnet (Alchemy Premium)
- **Lido oracle v7.0.0-beta.3:** Código fuente de referencia para análisis (NO modificar, en repo separado)

---

## Conceptos Clave

### Señal θ (Theta) — Política Monetaria Computacional (PMC)
- No es coercitiva. Es una señal *opt-in* de coordinación.
- Actúa como coeficiente de fricción económica para estabilizar el sistema bajo riesgo.
- **Vector:** `Θ_k = (θ^gas, θ^lat, θ^risk, θ^finality, θ^incentives)`
- **Derivada de:** Densidad Temporal del Epoch `D_k = f(MEV, liquidez, slashings, participación, congestión)`
- **Cálculo:** Grey Zone Score (Python puro, consensus spec) → emitir señal → derivar θ
- **Nota:** La optimización cuadrática con Qiskit es una línea de investigación futura,
  no una dependencia de producción. En producción se usa aritmética del consensus spec.

### Grey Zone Score (ex-QSR)
`gross_slashing_loss / (cl_rewards + burned_eth)`

Ratio que expresa la deuda oculta de slashings enmascarada por rewards positivos —
el escenario exacto que `safe_border.py` de Lido no detecta. Calculado off-chain
en Python puro, certificable por staking económico vía AVS (EigenLayer) en v2.

### ERC-8033 — Oráculo de Estabilidad
- Publica métricas agregadas on-chain: QSR, señal θ, densidad `D_k`
- Permite que smart contracts de otros agentes detecten anomalías
- Coordina pausas o ajustes defensivos antes de liquidaciones masivas
- Es la "señal de radio" de QUEST — un endpoint inmutable que dice: "Riesgo sistémico: 8/10"

### ERC-8004 — Reputación Soberana de Agentes
- Estándar de identidad/reputación para la economía de agentes autónomos
- QUEST extiende este estándar con la categoría *Sovereign Stability Agent*
- Emite "Scores de Integridad" según si los agentes respetan la solvencia sistémica
- Interfaz clave a implementar: `IERC8004QuestAware`

---

## Arquitectura Target (3 Capas)

```
┌─────────────────────────────────────────────────┐
│  CAPA 3: Economía de Agentes (ERC-8004)         │
│  Fondos de IA, bots liquidadores, Tesorerías    │
│  → Consumen señal θ → ajustan estrategia        │
│  → QUEST actualiza su reputación                │
└────────────────────┬────────────────────────────┘
                     │ lee θ / reporta
┌────────────────────▼────────────────────────────┐
│  CAPA 2: Contratos Base (On-Chain)              │
│  QUESTCore.sol + ERC-8033                       │
│  → Almacena PMC (θ) y métricas D_k             │
│  → Permissionless, no coercitivo               │
│  → Futuro: L1 o L2 base                        │
└────────────────────┬────────────────────────────┘
                     │ publica QSR / θ
┌────────────────────▼────────────────────────────┐
│  CAPA 1: Cómputo Off-Chain (Oracle Node)        │
│  Python + Qiskit (quantum_env)                  │
│  → Lee Execution Layer (TVL, reservas)          │
│  → Lee Consensus Layer (slashings, rewards)     │
│  → Resuelve Hamiltoniano → emite QSR            │
│  → Futuro: AVS en EigenLayer                   │
└─────────────────────────────────────────────────┘
```

---

## Decisiones de Arquitectura Ya Tomadas (No reabrir)

1. **AVS sobre EIP directo:** QUEST se construirá como AVS en EigenLayer en lugar de
   pugnar por aprobación de ERC-8033 como EIP oficial (proceso demasiado largo).

2. **Branding cuántico acotado al whitepaper:** En código y contratos usar terminología
   de "Optimización Cuadrática de Solvencia" y "Pruebas de Estrés Computacional".
   Reservar "Hamiltoniano", "Topología de la verdad" para el whitepaper/manifiesto.

3. **Off-chain computation obligatorio:** Qiskit no puede correr en la EVM. La capa de
   cómputo siempre será off-chain, certificada por staking económico (AVS).

4. **Permissionless por diseño:** QUEST no pausa ni coerciona. Solo emite señales.
   Los agentes optan por reaccionar a θ a cambio de mejor reputación ERC-8004.

---

## Hoja de Ruta Inmediata (Próximos pasos)

### Fase 1 — Risk Engine (COMPLETADA)
- [x] `data_pipeline.py`: ingesta Beacon REST API (ChainSafe Lodestar) + Alchemy
- [x] `lrt_risk_model.py`: Grey Zone Score (Python puro, consensus spec)
- [x] `quest.proto` + `grpc_server.py`: servicio gRPC SystemicRiskOracle
- [x] Deploy en GCP Cloud Run (`quest-api` + `quest-risk-engine`)
- [x] Dashboard público en Vercel

### Fase 2 — Contratos Base (Sepolia)
- [x] Refactorizar `QUESTCore.sol`: `reportEpochMetrics(...)`, `publishGreyZoneScore(θ)`, `updateAgentReputation(...)`
- [x] Implementar `IERC8004QuestAware` + `IERC8033` con terminología Grey Zone Score
- [x] Tests Foundry (`test/QUESTCore.t.sol`) — 10 casos cubriendo happy path + access control
- [x] Deploy script (`script/Deploy.s.sol`) + `foundry.toml` para Sepolia
- [x] `forge install` (forge-std v1.15.0) + `forge test` 10/10 en verde
- [x] Desplegar en Sepolia — bloque 10648557, gas: 1,148,831

### Fase 3 — AVS Node (COMPLETADA)
- [x] `quest-avs-node/` en Go — trusted oracle operator
- [x] Lee `quest-api/api/status` → convierte → publica on-chain
- [x] `QUESTCore.reportEpochMetrics` + `publishGreyZoneScore` cada epoch (~384s)
- [x] Deploy en Cloud Run (`quest-avs-node`, min-instances=1)
- [x] Primera tx en Sepolia — Epoch 440789 | score=0.0 | HEALTHY
  - reportEpochMetrics: `0xd6afe896de3bd8d848da7818acc8eac9c00197c7f4b7b84c87cd8b714c29696e`
  - publishGreyZoneScore: `0xa30b1fbd5afb0c625ddede391614607364902988f9cc8ea2821f6c0d6e091ba7`

### Fase 4 — Grants
- [ ] Ethereum Foundation ESP
- [ ] EigenLayer Foundation
- [ ] Lido Grants Program

---

## Contexto Paralelo

Este proyecto corre en paralelo a **Abu Oracle** (plataforma de astrología computacional).
No mezclar contextos. Si aparece código de Abu Oracle / Lilly Engine en este repo, es un error.

---

*Última actualización del contexto: Abril 2026*
*Fuente primaria: NotebookLM (documentación QUEST completa) + análisis del repo*
