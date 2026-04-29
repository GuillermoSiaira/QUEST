---
name: Research Strategy — Ecosistema Conceptual
description: Estrategia de investigación — nueva dirección (diseño de agentes + λ heterogeneity) y posicionamiento en la literatura
type: strategy
estado: activo
actualizado: 2026-04-25
tags: [estrategia, publicacion, papers, ecosistema, posicionamiento, agentes]
---

# Estrategia de Investigación — QUEST

---

## Pivote (Apr 2026)

El framing original centrado en el gap de `safe_border.py` en Lido fue descartado. La vulnerabilidad existe, pero no es riesgosa en sí misma: el oracle de Lido no habría fallado en mayo 2022 (confirmado por el backtest histórico — GZS diario ≈ 0.0003 durante el depeg). Perseguir ese argumento no rinde.

**Nueva dirección**: diseño de agentes autónomos basado en teoría económica. La pregunta central:

> ¿Cuáles son las señales que debe emitir un coordinador de agentes para que la dinámica del grupo sea estable en el largo plazo y con crecimiento sostenido?

QUEST pasa de "oracle macroprudencial de Lido" a **infraestructura de señal para coordinación de agentes autónomos en DeFi**.

---

## La tesis central

**La heterogeneidad de λ (aversión al riesgo) es una condición de estabilidad sistémica.**

Mientras los agentes mantengan distribuciones de λ suficientemente dispersas, la salida ante señales de stress es escalonada → el sistema absorbe el shock. Cuando F(λ,t) colapsa (todos los agentes con el mismo λ alto), la salida es simultánea → corrida.

**Corolario sobre diseño de señales**: existe un umbral de precisión σ* tal que señales más precisas que σ* homogenizan F(λ) → inestabilidad. Señales menos precisas preservan la heterogeneidad → estabilidad.

Esto conecta Morris-Shin (2002) con dinámica de replicadores (ESS) en un setting donde los parámetros del modelo son observables on-chain.

---

## Cadena causal

```
Señal pública s(t) emitida por QUEST (GZS cada epoch)
  ↓
Agente con λ_i computa α*(λ_i, s) = max(0, E(R) / λ_i·σ²(s))
  ↓
Si F(λ) heterogénea: αs diferenciados → salida escalonada → absorción
Si F(λ) homogénea:   αs idénticos   → salida simultánea → corrida
  ↓
Distribución F(λ,t) evoluciona via replicador:
  ẋ(λ) = x(λ)·[r(λ,s) − r̄]
  ↓
ESS: distribución estacionaria con soporte no degenerado ← condición de estabilidad
```

---

## Evidencia empírica disponible

### Backtest histórico (completado)

`risk-engine/backtest_historical_gzs.py` reconstruyó el GZS para Aug 2021 – Apr 2026 usando Xatu (DuckDB sobre parquet remoto de EthPandaOps).

**Resultado clave**: GZS = 0.0003 durante mayo 2022 (depeg stETH). El consensus layer no estaba en stress — era una crisis de mercado. El oracle de Lido habría funcionado correctamente. Esto demuestra **especificidad**: la señal no da falsos positivos ante shocks de mercado.

**Pico histórico real**: 14 Nov 2023 — 99 validadores slasheados — GZS epoch-peak = 9.0 (CRITICAL). Un evento real del consensus layer.

### Simulación de agentes (completado)

`agents/simulate_coordination.py` simula N=1000 agentes con:
- Población A: λ ~ Uniform[0.2, 1.8] (heterogénea)
- Población B: λ = 1.0 constante (homogénea, mismo promedio)

Bajo stress peak (GZS ≈ 1.07):
- Piso α heterogéneo: **0.347**
- Piso α homogéneo: **0.256**
- Diferencia: +35% — la distribución importa más que el promedio

`agents/aggregate_exposure.png` — gráfico de la tesis, presentable.

### Empírico pendiente (Paper 2)

Dune Analytics query para trackear top 500-1000 wallets stETH por tamaño de posición, 2021-2023. Observable:
- α̂(t) = fracción de portfolio en stETH por wallet
- λ̂ = (1 − α̂)·2·E(R) / σ²(s(t))
- Var(F̂(λ,t)) → test de colapso durante mayo 2022

---

## Plan de publicación: 2 papers

### Paper 1 — EN PROCESO: ethresear.ch / workshop

**"Macroprudential Signals for Autonomous Agents: λ-Heterogeneity as a Stability Condition"**

Secciones:
1. **Problem** — EIP-7702 + agentes AI en DeFi: ¿qué garantiza que su coordinación sea estable?
2. **Model** — utilidad media-varianza con σ²(GZS); α*(λ, s); distribución F(λ,t)
3. **Theory** — dinámica de replicadores → ESS con soporte no degenerado; umbral σ*
4. **Evidence** — simulación (agents/); backtest de especificidad (risk-engine/backtest_historical_gzs.py)
5. **Implications** — diseño de oracles; heterogeneidad como objetivo de política; respuesta a AI Agents 2026

**Estado**: framework conceptual completo, simulación funcional, backtest completado. Falta: formalización matemática §3, datos empíricos §4, escritura.

### Paper 2 — BLOQUEADO POR DATOS: empírico

**"λ-Heterogeneity Collapse During the stETH Depeg: On-Chain Evidence"**

- Dune Analytics: α̂ por wallet por semana (2021-2023)
- Var(F̂(λ,t)) durante y después de mayo 2022
- Test: ¿el colapso de heterogeneidad precedió o siguió al depeg?

**Estado**: metodología definida. Bloqueado por query de Dune (~1-2 días de trabajo).

---

## Posicionamiento en la literatura

| Paper | Gap que QUEST llena |
|-------|---------------------|
| **Morris-Shin (2002)** | Extiende su resultado a setting evolutivo (replicador) y DeFi medible |
| **AI Agents 2026 (2603.13942)** | Responde directamente: λ heterogéneo produce salida escalonada, no simultánea |
| **He et al. (2401.08610)** | GZS es la señal temprana antes de las cascadas que documentan |
| **Scharnowski (2025)** | Backtest ubica mayo 2022 como no-evento en el consensus layer → especificidad |
| **Gogol SoK (2024)** | QUEST es el AVS de monitoreo sistémico que el SoK implica pero no propone |

---

## Artefactos para grants / demos

| Artefacto | Ubicación | Uso |
|-----------|-----------|-----|
| Agente autónomo live | `agents/quest_agent.py` | Demo en presentaciones, `--demo` mode |
| Simulación de coordinación | `agents/simulate_coordination.py` | Figura central del paper |
| Gráfico de la tesis | `agents/aggregate_exposure.png` | Grant applications, slides |
| Backtest histórico | `risk-engine/backtest_historical_gzs.py` | Evidencia de especificidad |
| API live | quest-api-oo2ixbxsba-uc.a.run.app | Demo, integración de agentes reales |

---

## Conexiones en vault

→ [[open_questions]] — Q4 y Q5 reformuladas bajo el nuevo frame
→ [[positioning_table]] — tabla comparativa con 8 papers
→ [[grant_roadmap]] — argumentos por grant actualizados
→ [[utility_function]] — función de utilidad base del modelo
→ [[coordination_result]] — resultado de Nash subyacente
