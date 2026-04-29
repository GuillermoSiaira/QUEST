---
name: 00_index
description: Mapa central del vault — índice navegable de todos los nodos de QUEST
tipo: index
version: 2026-04-25
estado: activo
tags: [index, mapa, navegacion]
---

# QUEST — Knowledge Vault

Infraestructura de señal para coordinación de agentes autónomos en DeFi. Publica el **Grey Zone Score** cada epoch (~384s) como señal pública para que agentes con λ heterogéneo coordinen exposición sin coerción — tesis: la heterogeneidad de aversión al riesgo es una condición de estabilidad sistémica.

**Repo**: `D:\projects\QUEST` · **API**: `quest-api-oo2ixbxsba-uc.a.run.app` · **Dashboard**: `quest-orcin-sigma.vercel.app`

---

## Mapa visual

→ Abrir [[QUEST_canvas]] para ver el flujo del paper en formato canvas.

---

## Plan de investigación activo

→ [[research_plan]] — **"Homo Silicus in the Market"** — Aggregate Rationality in Multi-Agent AI Systems. Estado del arte, hipótesis, bibliografía, plan de trabajo 6 meses.

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
| [[dune_query]] | **⭐ SIGUIENTE PASO**: SQL para estimar λ̂ por wallet on-chain — desbloquea Paper 2 |
| [[historical_dataset]] | Fuentes Xatu/DuckDB para backtest del consensus layer (completado) |

---

## 05 — Grants

| Documento | Descripción |
|-----------|-------------|
| [[ethresear_v2]] | **Draft completo** — "Macroprudential Signals for Autonomous Agents" |
| [[grant_roadmap]] | Estado de las 4 aplicaciones enviadas + pendientes |
| [[feedback_received]] | **Registro de feedback** — EF/Boris, Lido bug bounty + plan de respuesta |

---

## 06 — Preguntas Abiertas

| Documento | Descripción |
|-----------|-------------|
| [[open_questions]] | Las 5 preguntas para la comunidad de ethresear.ch |

---

## 07 — Literatura & Posicionamiento

### Estrategia & Posicionamiento

| Documento | Descripción |
|-----------|-------------|
| [[positioning_table]] | **⭐ Tabla comparativa**: 8 papers vs. QUEST — qué identifican, qué proponen, qué gap QUEST llena |
| [[research_strategy]] | **⭐ Estrategia**: 3 papers en secuencia, cómo se citan, argumentos por grant, respuesta al backtest |

### Racionalidad Agregada en AI (Programa de investigación nuevo)

| Documento | Descripción |
|-----------|-------------|
| [[smd_theorem]] | SMD (Sonnenschein-Mantel-Debreu 1973-74) — racionalidad individual ≠ racionalidad agregada; fundamento teórico |
| [[morris_shin_2002]] | Morris & Shin (AER 2002) — señales públicas precisas desestabilizan; umbral σ*; diseño de GZS |
| [[horton_homo_silicus_2023]] | Horton et al. (2023, arXiv:2301.07543) — "Homo Silicus"; LLMs satisfacen WARP individualmente |
| [[aher_turing_2023]] | Aher et al. (ICML 2023, arXiv:2208.10264) — hyper-accuracy distortion; LLMs menos diversos que humanos |
| [[econagent_2024]] | Li et al. (ACL 2024, arXiv:2310.10436) — LLMs reproducen Phillips Curve y Ley de Okun |
| [[sparks_rationality_2026]] | Tak et al. (2026, arXiv:2601.22329) — reasoning mejora racionalidad individual pero amplifica steering afectivo |
| [[rationality_survey_naacl_2025]] | Jiang et al. (NAACL 2025, arXiv:2406.00252) — survey racionalidad en LLM agents; gap agregado no abordado |
| [[ai_agents_financial_markets_2026]] | Gong (2026, arXiv:2603.13942) — AFMM; homogeneidad = vulnerabilidad; gap explícito sobre heterogeneidad óptima |
| [[machine_spirits_2026]] | Saxena et al. (2026, arXiv:2604.18602) — 15 LLMs en mercados; inestabilidad endógena con heterogeneidad |

### LST / Staking (Paper 1 / fundamentos GZS)

| Documento | Descripción |
|-----------|-------------|
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
