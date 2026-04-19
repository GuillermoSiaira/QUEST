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
| `quest-api` | https://quest-api-oo2ixbxsba-uc.a.run.app | ✅ Running |
| `quest-risk-engine` | https://quest-risk-engine-oo2ixbxsba-uc.a.run.app | ✅ Running (gRPC, privado) |
| `quest-avs-node` | https://quest-avs-node-oo2ixbxsba-uc.a.run.app | ✅ Running (privado) |

### Contratos desplegados:
| Contrato | Red | Address | Tx |
|---|---|---|---|
| `QUESTCore` | Sepolia | `0xE81C6B16ecbEC8E4Aadc963e82B27c10c4ab10e7` | `0x48ebe0a7...e8ded2` |
| `QUESTAwareProtocol` | Sepolia | `0xD693C783AbDCe3B53b2C33D8fEB0ff4E70f12735` | verified ✅ |

Operator: `0xBb3272F387dE5A2c2e3906d24EfaC460a7013f2C`

### Persistencia (3 capas descentralizadas):
| Capa | Proveedor | Campo en Firestore | Estado |
|---|---|---|---|
| Hot storage | GCP Firestore (`epoch_snapshots`) | — | ✅ Live |
| IPFS | Pinata (`pinata-jwt` en Secret Manager) | `ipfs_cid` | ✅ Live desde 2026-04-19 |
| Filecoin | Lighthouse (`lighthouse-api-key` en Secret Manager) | `filecoin_cid` | ✅ Live desde 2026-04-19 |

Cada epoch genera: `Beacon Chain → QUEST → Firestore + IPFS (CIDv1) + Filecoin (storage deal)`
Service account: `299259685359-compute@developer.gserviceaccount.com` con `roles/datastore.user`

### Bugs corregidos (2026-04-19) — Storage descentralizado

**1. epoch_rewards_gwei siempre None**
Root cause: El pipeline pollaba cada 60s pero un epoch dura ~6.4 min. `epoch_rewards_gwei`
solo se calculaba en el primer poll del epoch nuevo; los polls 2-6 lo sobreescribían con None.
Fix: Guard `last_emitted_epoch` en `run()` — callbacks solo se invocan cuando el epoch avanza.
Efecto secundario positivo: 1 write/epoch a Firestore en lugar de 6-7 (~85% reducción de costos).

**2. Pinata V3 — upload del wrapper en lugar del JSON canónico**
Root cause: Se pasaba `_build_pinata_payload(status)` como contenido del archivo, resultando en
`{"pinataContent": {...}, "pinataMetadata": {...}}` almacenado en IPFS en lugar del JSON limpio.
Fix: El archivo subido es `_build_snapshot_content(status)` — JSON canónico `{schema, network, data}`.
Adicionalmente: añadir campo `network=public` al multipart form para que el gateway sirva el contenido
(sin este campo, Pinata V3 crea archivos privados y el gateway devuelve 403/timeout).

**3. Lighthouse — CID parsing incorrecto**
Root cause: Se parseaba `data.get("data", {}).get("Hash")` pero Lighthouse `/api/v0/add` devuelve
`{"Name": ..., "Hash": ..., "Size": ...}` en la raíz, sin wrapper `data`.
Fix: `cid = data.get("Hash")`. Timeout aumentado de 60s a 120s (Cloud Run → Lighthouse es más lento).

**4. epoch_rewards_gwei negativo (-408 ETH) con 0 slashings**
Root cause: Ruido de timing en la Beacon API — el balance baseline se capturaba de un estado
de epoch distinto al de los rewards, produciendo un delta negativo imposible.
Fix: Guard en `data_pipeline.py` — si `epoch_rewards_gwei < 0` y `slashed_count == 0`, descartar como None.

**5. Gateway URLs incorrectos**
- `gateway.lighthouse.storage` no resuelve DNS públicamente. URL correcta: `files.lighthouse.storage/viewFile/<CID>`
- `dweb.link` devuelve 504 para CIDs de Pinata (Pinata almacena en nodos IPFS privados, no anuncia al DHT público).
  Solo `gateway.pinata.cloud/ipfs/<CID>` sirve el contenido.

**6. StorageProof.tsx — `linkTitle` no destructurado**
Root cause: La prop `linkTitle` estaba declarada en el tipo pero no en la destructuración del componente,
causando `Cannot find name 'linkTitle'` en el type-check de Next.js 16 (Turbopack).
Fix: añadir `linkTitle` a la destructuración de parámetros.

**7. EpochPage — useParams sin tipo genérico**
Root cause: En Next.js 15+, `useParams()` sin tipo genérico devuelve `{}`, haciendo que `params.epoch`
sea un error TypeScript.
Fix: `useParams<{ epoch: string }>()`.

### Módulos del risk-engine:
| Archivo | Descripción |
|---|---|
| `risk-engine/data_pipeline.py` | Ingesta Beacon REST API + Alchemy → EpochSnapshot |
| `risk-engine/lrt_risk_model.py` | Grey Zone Score desde EpochSnapshot (Python puro) |
| `risk-engine/consensus_constants.py` | Constantes del consensus spec de Ethereum |
| `risk-engine/grpc_server.py` | Servidor gRPC: SystemicRiskOracle.CalculateGreyZoneScore |
| `risk-engine/quest.proto` | Contrato gRPC (proto3) |
| `risk-engine/test_historical_grey_zone.py` | Validación histórica del Grey Zone Score vs Firestore (genera CSV) |
| `test/TheSmartExit.t.sol` | PoC en Solidity (Foundry): demuestra el vector de arbitraje en Lido |

### Módulos de la API:
| Archivo | Descripción |
|---|---|
| `api/main.py` | FastAPI: REST + WebSocket + pipeline callbacks + `/api/epoch/{n}` |
| `api/db.py` | Persistencia Firestore: save, load, update_epoch_cid, update_epoch_filecoin |
| `api/ipfs_store.py` | Storage descentralizado: Pinata V3 (IPFS) + Lighthouse (Filecoin) |
| `api/models.py` | Pydantic: EpochStatus (+ ipfs_cid, filecoin_cid), RiskAssessment, FeedMessage |

**Endpoints REST:**
| Método | Path | Descripción |
|---|---|---|
| GET | `/health` | Healthcheck + conteo de snapshots en memoria |
| GET | `/api/status` | Último EpochStatus disponible |
| GET | `/api/history?n=50` | Últimos n snapshots (max 200) |
| GET | `/api/epoch/{epoch_number}` | Epoch concreto por número (memoria → Firestore) |
| WS  | `/ws/feed` | Stream en tiempo real (FeedMessage JSON) |

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

### Fase 3.5 — Dashboard & Persistencia (COMPLETADA, 2026-04-19)
- [x] `StorageProof.tsx` — barra de 3 capas (Firestore · IPFS · Filecoin) con dots de estado y CID links
- [x] `EpochHeader.tsx` — rediseño: borde de acento por risk level, stat labels mejorados
- [x] `app/epoch/[epoch]/page.tsx` — epoch viewer propio con Download JSON funcional
  - Reemplaza Lighthouse viewer (cuyo botón Download estaba roto)
  - Enlace Filecoin en StorageProof apunta a `/epoch/{n}` en lugar del viewer de Lighthouse
- [x] `app/page.tsx` — StorageProof integrado entre EpochHeader y Analysis; layout `lg:grid-cols-5`
- [x] Stack de storage completamente operativo: cada epoch escribe en paralelo a IPFS + Filecoin
  - `asyncio.gather(_pin_ipfs(), _pin_filecoin())` — ~2s vs ~4s secuencial
  - CIDs adjuntados al EpochStatus via `model_copy(update=...)` antes del broadcast WebSocket
  - `EpochStatus.ipfs_cid` y `EpochStatus.filecoin_cid` persistidos en Firestore y devueltos por la API

### Fase 4 — Grants (en curso, 2026-04-19)
- [ ] **EigenLayer Foundation** — One-pager redactado, pendiente post en forum.eigenlayer.xyz
- [ ] **Filecoin Open Grants** — Hasta $50K, aplicación continua via GitHub issues. One-pager listo.
- [ ] **IPFS Utility Grants** — Próxima ronda ~Q3 2026. Fit perfecto: domain-specific IPFS tooling.
- [ ] Ethereum Foundation ESP
- [ ] Lido Grants Program
- [ ] Pinata — Contacto directo vía Discord (no tienen portal público de grants)

### Fase 5 — Descentralización completa (próximos pasos)
- [ ] Publicar `filecoin_cid` on-chain en `QUESTCore.sol` → audit trail completamente verificable
- [ ] Backfill histórico: pinear los 1,243+ epochs existentes a IPFS + Filecoin
- [ ] Migrar AVS node de GCP a Pinata OpenClaw Agents
- [ ] MEV-Boost data feed (v2): reemplazar `burned_eth` proxy con datos reales de flashbots

### Fase 6 — Cobertura multi-protocolo (v2)
Hoy QUEST monitorea el Consensus Layer de Ethereum en su totalidad (métricas de red).
La Fase 6 desagrega el riesgo por protocolo LST/LRT:

**TVL por protocolo** (via Alchemy — lectura de contratos on-chain):
- [ ] Rocket Pool: `rETH.totalSupply()` × precio
- [ ] EtherFi: `EETH.totalValueOutOfLp()`
- [ ] Swell: `swETH.totalSupply()` × precio
- [ ] Kelp: `LRTDepositPool.getTotalAssetDeposits()`

**Slashings atribuidos por protocolo**:
- [ ] Filtrar validadores slasheados por withdrawal credentials → asignar pérdida a cada protocolo
- [ ] Nuevos campos en `EpochSnapshot`: `lido_slashing_eth`, `rocketpool_slashing_eth`, etc.

**Grey Zone Score por protocolo**:
- [ ] `grey_zone_lido = lido_slashing_loss / lido_cl_rewards`
- [ ] Idem para Rocket Pool, EtherFi, Swell, Kelp
- [ ] `RiskAssessment` extendido con scores individuales + score de red (actual)
- [ ] Dashboard: tabla comparativa de riesgo por protocolo
- [ ] API: `GET /api/protocols` → scores actuales por protocolo

**Nota:** El score de red actual (Fase 1) sigue siendo la señal primaria para el AVS y los contratos.
Los scores por protocolo son la capa de análisis granular para investigadores y el Lido Grants Program.

---

## Contexto Paralelo

Este proyecto corre en paralelo a **Abu Oracle** (plataforma de astrología computacional).
No mezclar contextos. Si aparece código de Abu Oracle / Lilly Engine en este repo, es un error.

---

*Última actualización del contexto: 2026-04-19 (post Fase 3.5 — storage descentralizado completo)*
*Fuente primaria: código en producción + análisis del repo*
