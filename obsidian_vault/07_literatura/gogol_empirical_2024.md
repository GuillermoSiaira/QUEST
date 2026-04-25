---
name: Gogol 2024 — Empirical & Theoretical Analysis of LST
description: Primer paper que clasifica implementaciones de LSTs y analiza su performance histórico — rebase vs reward vs dual token
type: literature
arxiv: 2401.16353
año: 2024
autores: Gogol, Kraner et al.
tags: [literatura, LST, clasificacion, peg-stability, MEV, taxonomia]
---

# Gogol et al. (2024) — Empirical and Theoretical Analysis of Liquid Staking Protocols

**arXiv: 2401.16353** | Semantic Scholar: [enlace](https://www.semanticscholar.org/paper/Empirical-and-Theoretical-Analysis-of-Liquid-Gogol-Kraner/631a78de8f1b7a8531c365bdc258f2a5668b5209)

---

## Qué estudia

Primer paper que sistemáticamente **clasifica las implementaciones de LSTs** y analiza la performance histórica de los principales tokens vs. staking directo para los mayores blockchains PoS. Investiga el impacto de la centralización, MEV, y la migración de Ethereum de PoW a PoS.

---

## Problema que identifica

Antes de este paper no existía una taxonomía formal de LSTs. Las diferencias de diseño (rebase vs. reward vs. dual token) producen **comportamientos distintos de peg stability y yield** que los participantes del mercado no tenían formalizados.

---

## Solución propuesta

**Taxonomía de implementaciones LST:**

| Tipo | Mecanismo | Ejemplo |
|------|-----------|---------|
| Rebase | Token balance reajusta cada epoch (1 stETH ≈ 1 ETH permanentemente) | Lido stETH |
| Reward | Precio del token sube, cantidad fija | rETH (Rocket Pool) |
| Dual token | Token staking + token de reward separados | varios |

**Hallazgos clave:**
- LSTs con gobernanza **centralizada** son más eficientes en tracking de rewards
- Eventos de mercado y choices de diseño afectan peg stability significativamente
- MEV tiene impacto documentado en el performance de los tokens

---

## Evidencia empírica

- Análisis histórico de performance de principales LSTs (Lido, Rocket Pool, etc.)
- Comparación yield LST vs. staking directo
- Análisis del impacto del Merge en performance

---

## Gap que QUEST llena

Gogol clasifica los **tipos de LST** y analiza su performance histórico. No existe en este paper ningún mecanismo para detectar cuándo el riesgo de slashing está siendo enmascarado por recompensas. QUEST añade una **capa de monitoreo en tiempo real** sobre los protocolos que Gogol clasifica.

**Inserción**: QUEST puede usar la taxonomía de Gogol para extender el GZS a un score por tipo de LST (la Pregunta Abierta Q1 del paper). El grey zone es específicamente un problema del modelo rebase (stETH), donde el peg artificial oculta la deuda de slashing.

---

## Conexiones en vault

→ [[grey_zone_score]] — GZS es la señal que falta en el análisis de Gogol
→ [[open_questions#Q1]] — por-protocolo GZS requiere la taxonomía de Gogol
