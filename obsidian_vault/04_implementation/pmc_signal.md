---
tags: [implementation, pmc, signal]
tipo: referencia
estado: activo
---

# Señal PMC — Vector 5D

Más allá del [[grey_zone_score|GZS escalar]], QUEST publica un **vector PMC (Polynomial Monetary Control)** — 5 dimensiones de riesgo ortogonales, publicadas cada epoch.

---

## El vector

$$\theta \in [0, 10000]^5$$

| Dimensión | Símbolo | Significado |
|-----------|---------|-------------|
| Riesgo de slashing | $\theta_{risk}$ | Ratio slashing/rewards (= GZS normalizado) |
| Presión de gas | $\theta_{gas}$ | Presión del mercado de gas (base fee vs baseline) |
| Latencia de datos | $\theta_{latency}$ | Delay de propagación de datos del Beacon |
| Riesgo de finalidad | $\theta_{finality}$ | Riesgo de finalidad (tasa de participación) |
| Desequilibrio de incentivos | $\theta_{incentives}$ | Desbalance MEV/issuance |

---

## Por qué 5 dimensiones

Un solo número (el GZS) no captura todos los vectores de riesgo relevantes. La analogía macroprudencial: los bancos centrales publican múltiples indicadores (ratios de adecuación de capital, ratios de cobertura de liquidez) — diferentes actores del sistema financiero consumen diferentes dimensiones.

Un protocolo de lending puede ponderar $\theta_{risk}$ fuertemente. Un DEX puede ponderar $\theta_{gas}$ y $\theta_{latency}$.

---

## Composabilidad

El vector está diseñado para ser composable: los protocolos definen sus propios pesos:

$$\text{RiskScore}_{\text{protocol}} = \sum_{i} w_i \cdot \theta_i$$

Donde $w_i$ es la ponderación del protocolo para la dimensión $i$.

---

## Estado actual

En v1, el GZS escalar ($\theta_{risk}$) es el componente publicado y verificable on-chain. Los otros 4 componentes están calculados en el risk-engine pero no todos están validados con la misma precisión.

→ Ver [[architecture]] para el pipeline de cálculo
