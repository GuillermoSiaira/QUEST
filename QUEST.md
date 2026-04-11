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

**Repo local:** `D:\projects\lido-oracle-7.0.0-beta.3`

### Código existente (propio):
| Archivo | Descripción |
|---|---|
| `quantum_exploit.py` | PoC: optimización cuadrática con Qiskit. Mapea estado del protocolo a Hamiltoniano de Ising para encontrar vectores de insolvencia. Calcula QSR. |
| `lrt_risk_model.py` | Modelo de riesgo cuadrático (en `quantum_env`) |
| `test/TheSmartExit.t.sol` | PoC en Solidity (Foundry): demuestra el vector de arbitraje en Lido |

### Entornos configurados:
- **Python:** `quantum_env` con Qiskit
- **Foundry:** Configurado con fork de Mainnet (Alchemy Premium)
- **Lido oracle v7.0.0-beta.3:** Código fuente de referencia para análisis (NO modificar)

---

## Conceptos Clave

### Señal θ (Theta) — Política Monetaria Computacional (PMC)
- No es coercitiva. Es una señal *opt-in* de coordinación.
- Actúa como coeficiente de fricción económica para estabilizar el sistema bajo riesgo.
- **Vector:** `Θ_k = (θ^gas, θ^lat, θ^risk, θ^finality, θ^incentives)`
- **Derivada de:** Densidad Temporal del Epoch `D_k = f(MEV, liquidez, slashings, participación, congestión)`
- **Cálculo:** Resolver el Hamiltoniano de solvencia via Qiskit → emitir QSR → derivar θ

### QSR — Quantum Solvency Ratio
Ratio que expresa la "superposición de estados" (rentabilidad aparente vs. deuda oculta)
que la lógica plana de la EVM ignora. Calculado off-chain con optimización cuadrática.

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

### Fase 1 — Limpieza y Estandarización (Ahora)
- [ ] Refactorizar `QUESTCore.sol`: funciones `reportEpochMetrics(...)`, `publishPMC(θ)`, `updateAgentReputation(...)`
- [ ] Crear interfaz `IERC8004QuestAware`
- [ ] Modularizar `lrt_risk_model.py` como microservicio funcional

### Fase 2 — Testnet (Sepolia)
- [ ] Desplegar QUESTCore.sol en Sepolia
- [ ] Conectar oracle node Python → contrato

### Fase 3 — AVS / Whitepaper
- [ ] Diseño del AVS en EigenLayer
- [ ] Redactar EIP/Whitepaper final integrando concepto AVS + Economía de Agentes

---

## Contexto Paralelo

Este proyecto corre en paralelo a **Abu Oracle** (plataforma de astrología computacional).
No mezclar contextos. Si aparece código de Abu Oracle / Lilly Engine en este repo, es un error.

---

*Última actualización del contexto: Abril 2026*
*Fuente primaria: NotebookLM (documentación QUEST completa) + análisis del repo*
