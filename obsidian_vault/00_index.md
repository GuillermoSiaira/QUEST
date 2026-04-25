---
name: 00_index
description: Mapa central del vault — índice navegable de todos los nodos de QUEST
tipo: index
version: 2026-04-24
estado: activo
tags: [index, mapa, navegacion]
---

# QUEST — Knowledge Vault

Oracle macroprudencial para el Consensus Layer de Ethereum. Publica el **Grey Zone Score** cada epoch (~384s) y propone un framework de utilidad para que agentes DeFi coordinen riesgo sistémico sin coerción.

**Repo**: `D:\projects\QUEST` · **API**: `quest-api-oo2ixbxsba-uc.a.run.app` · **Dashboard**: `quest-orcin-sigma.vercel.app`

---

## Mapa visual

→ Abrir [[QUEST_canvas]] para ver el flujo del paper en formato canvas.

---

## ⚡ Los 3 Programas (desarrollo activo)

El paper de ethresear.ch establece el framework. Los **3 programas** lo convierten en producto, infraestructura y agenda académica.

| Programa | Pregunta que responde | Estado |
|----------|----------------------|--------|
| [[program_economic]] | ¿Quién paga, qué compra, por qué? | 🟡 Desarrollo — gap: elegir cliente v1 |
| [[program_technical]] | ¿Qué construimos para vender eso? | 🟡 Esqueleto — gap: dataset histórico |
| [[program_research]] | ¿Qué publicamos y dónde? | 🟡 Esqueleto — gap: lectura académica |

**Regla de orden**: sin el económico resuelto, los otros dos son humo.

---

## 01 — Señal

| Documento | Descripción |
|-----------|-------------|
| [[grey_zone_score]] | Definición formal del GZS: `L_s / (R_cl + R_el)`, tabla de estados, calibración |
| [[safe_border_gap]] | El gap estructural en `safe_border.py` de Lido que motiva QUEST |

---

## 02 — Framework de Utilidad

| Documento | Descripción |
|-----------|-------------|
| [[utility_function]] | `U = E(R) − (λ/2)·σ_base²·e^(k·GZS)` — función de utilidad media-varianza |
| [[exposure_ratio]] | `α = max(0, 1 − λσ²/2E(R))` — tabla de exposición por nivel de GZS |
| [[capm_frontier]] | Frontera eficiente CAPM-style: β_GZS como parámetro de diseño |
| [[utility_api]] | **⭐ Extensión**: API de funciones de utilidad calibradas para otros agentes — axiomas de la teoría del consumidor como infraestructura |

---

## 03 — Resultado de Coordinación

| Documento | Descripción |
|-----------|-------------|
| [[coordination_result]] | Estrategia dominante + equilibrio de Nash de 2 agentes |
| [[free_rider_inversion]] | Por qué la estructura free-rider se invierte con agentes QUEST-aware |

---

## 04 — Implementación

| Documento | Descripción |
|-----------|-------------|
| [[architecture]] | Stack técnico: risk-engine → API → AVS → contratos Sepolia |
| [[contracts]] | QUESTCore.sol, QUESTAwareProtocol.sol, QUESTAgent.sol — addresses y ABIs |
| [[pmc_signal]] | Vector PMC 5D: θ_risk, θ_gas, θ_latency, θ_finality, θ_incentives |

---

## 05 — Grants

| Documento | Descripción |
|-----------|-------------|
| [[ethresear_v2]] | **Draft completo** — "Macroprudential Signals for Autonomous Agents" |
| [[grant_roadmap]] | Estado de las 4 aplicaciones enviadas + pendientes |

---

## 06 — Preguntas Abiertas

| Documento | Descripción |
|-----------|-------------|
| [[open_questions]] | Las 5 preguntas para la comunidad de ethresear.ch |

---

## 07 — Literatura & Posicionamiento

| Documento | Descripción |
|-----------|-------------|
| [[positioning_table]] | **⭐ Tabla comparativa**: 8 papers vs. QUEST — qué identifican, qué proponen, qué gap QUEST llena |
| [[research_strategy]] | **⭐ Estrategia**: 3 papers en secuencia, cómo se citan, argumentos por grant, respuesta al backtest |
| [[scharnowski_2025]] | Scharnowski (JFM 2025) — LST economics, basis, mayo 2022 como evento sistémico |
| [[gogol_empirical_2024]] | Gogol et al. (2401.16353) — taxonomía LST: rebase/reward/dual; peg stability |
| [[gogol_sok_2024]] | Gogol SoK (2404.00644) — framework unificado LSTs + restaking; slashing en pools |
| [[tzinas_zindros_2024]] | Tzinas & Zindros (2024) — problema principal-agente en LSTs; fungibilidad destruye alineación |
| [[he_leverage_2024]] | He et al. (2401.08610) — leverage staking cascadas 16x; 442 posiciones; 963 días |
| [[ai_agents_2026]] | arxiv 2603 (2026) — agentes AI correlacionados amplifican inestabilidad; objeción directa a Q5 |
| [[systemic_risk_review_2025]] | arxiv 2508 (2025) — literatura review riesgo sistémico TradFi/DeFi; ETH como hub |
| [[lido_v3_2025]] | Lido V3 WP (dic 2025) — oracle mejorado para fallos; grey zone NO resuelto en V3 |

---

## Parámetros de referencia (producción)

| Parámetro | Valor |
|-----------|-------|
| σ_base | 0.05 |
| k | ln(10) ≈ 2.303 |
| λ | 0.6 |
| E(R) | 0.0075 |
| Umbral Grey Zone | GZS ≥ 0.5 |
| Umbral Critical | GZS ≥ 1.0 |
| Epoch duration | ~384 segundos |
| Validadores activos | ~2.25M |
