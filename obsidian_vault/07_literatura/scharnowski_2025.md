---
name: Scharnowski 2025 — LST Economics
description: Primera investigación empírica de la economía de liquid staking tokens — basis, price discovery, implicaciones sistémicas
type: literature
doi: 10.1002/fut.22556
journal: Journal of Futures Markets (Wiley)
año: 2025
tags: [literatura, LST, basis, price-discovery, mayo-2022, sistémico]
---

# Scharnowski et al. (2025) — The Economics of Liquid Staking Derivatives

**Journal of Futures Markets** | DOI: 10.1002/fut.22556

---

## Qué estudia

Primera investigación empírica de las dinámicas de precio de liquid staking tokens (LSTs) — derivados que representan una fracción de ETH stakeado en un pool. Estudia el **liquid staking basis** (diferencia entre precio del token y el underlying), sus determinantes, y cómo los LSTs contribuyen al price discovery de las criptomonedas subyacentes.

---

## Problema que identifica

Los LSTs han crecido de USD 20M (ene 2021) a USD 15B (jul 2023). stETH representa >30% del stake total de Ethereum. A pesar de esa escala, **no existía análisis económico formal** de su precio ni de sus implicaciones sistémicas.

Nota textual del paper: *"liquid staking tokens played a prominent role in the turmoil in cryptocurrency markets starting May 2022 and may thus have implications for systemic risk within decentralized finance."*

---

## Solución propuesta

**Ninguna** — es un paper descriptivo/empírico. No propone mecanismos de mitigación de riesgo sistémico. Identifica 4 determinantes del basis:

1. **Staking rewards**: basis más ancho cuando LST ofrece menor yield relativo
2. **Concentration risk**: basis más ancho con mayor concentración de un proveedor
3. **Limits to arbitrage**: basis inversamente relacionado con liquidez del mercado secundario
4. **Behavioral factors**: basis correlacionado con sentiment e implied volatility

---

## Evidencia empírica

- Dataset: 3+ años de datos (enero 2021 – julio 2023 como mínimo)
- Análisis de basis diario Lido stETH vs ETH
- Información shares para price discovery (metodología Hasbrouck)
- LSTs contribuyen creciente fracción al price discovery — su importancia aumenta en el tiempo

---

## Literatura que cita (relevante para QUEST)

| Paper | Relevancia |
|-------|-----------|
| Gogol et al. (2401.16353) | Clasificación de LSTs → QUEST complementa con señal de riesgo en tiempo real |
| Tzinas & Zindros (2024) | Problema principal-agente en LSTs → QUEST detecta cuando produce riesgo sistémico |
| He et al. (2401.08610) | Leverage staking y cascadas → QUEST emite señal previa a esas cascadas |

---

## Gap que QUEST llena

Scharnowski documenta **qué** impulsa el basis y **cuándo** (mayo 2022) hay implicaciones sistémicas. No propone ningún mecanismo para detectar ni coordinar alrededor de ese riesgo. QUEST es la infraestructura que emite la señal que habría alertado a agentes antes del depeg de mayo 2022.

**Inserción**: QUEST puede citar a Scharnowski para motivar la necesidad del oracle — si los LSTs son sistémicamente relevantes (Scharnowski), y ningún oracle monitoreaba el riesgo de la capa de consenso (QUEST), el gap era estructural.

---

## Backtest implication

El evento de mayo 2022 que Scharnowski menciona como sistémicamente relevante es exactamente el target del backtest de QUEST. Si GZS hubiera estado operando en mayo 2022, habría emitido señal antes del depeg de stETH. Eso convierte el backtest en una **validación empírica directa** de la contribución sobre Scharnowski.

→ Ver [[historical_dataset]] para la estrategia de datos del backtest
