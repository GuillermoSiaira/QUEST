---
name: He et al. 2024 — Leverage Staking with LSDs
description: Primer modelo formal de leverage staking — Lido-Aave ecosystem; cascadas de liquidación hasta 16x; 442 posiciones reales
type: literature
arxiv: 2401.08610
año: 2024 (v4 actualizado)
autores: He et al.
tags: [literatura, leverage-staking, cascadas, Lido, Aave, stETH, liquidaciones, empirico]
---

# He et al. (2024) — Leverage Staking with Liquid Staking Derivatives: Opportunities and Risks

**arXiv: 2401.08610** | [PDF en eprint](https://eprint.iacr.org/2023/1842.pdf)

---

## Qué estudia

Primer estudio formal del **leverage staking**: estrategia iterativa de depositar stETH como colateral en Aave, pedir prestado ETH, y re-stakear en Lido — amplificando rendimientos pero también riesgos.

---

## Problema que identifica

El ecosistema Lido-Aave permite que usuarios construyan posiciones de leverage staking cuyo riesgo sistémico es:
1. **Invisible para los participantes individuales** (cada posición parece local)
2. **Amplificado exponencialmente** en stress: en simulaciones de depeg severo, la liquidación escaló 16x vs. escenario sin leverage
3. **Auto-reforzante**: la venta forzada de stETH presiona el precio, triggering más liquidaciones

---

## Solución propuesta

**Modelo formal** del proceso de leverage staking. No propone mecanismo de coordinación ni oracle. Proporciona:
- Formalización matemática del proceso iterativo de leverage
- Análisis de condiciones bajo las cuales emergen cascadas
- Stress test: 442 posiciones identificadas en 963 días (~537K ETH, ~$877M)

---

## Evidencia empírica (la más fuerte de toda la literatura)

| Métrica | Valor |
|---------|-------|
| Posiciones identificadas | 442 |
| Período de análisis | 963 días |
| Volumen total | ~537,123 ETH (~$877M) |
| % posiciones con APR > staking directo | 81.7% |
| Amplificación de liquidación en stress extremo | **16x** |

---

## Gap que QUEST llena

He et al. modelan **qué pasa cuando ya empezó la cascada**. QUEST emite señal **antes de que empiece**: el Grey Zone Score detecta el momento en que las condiciones de slashing+MEV crean vulnerabilidad sistémica, potencialmente antes de que el depeg trigger las liquidaciones de He et al.

**La cadena causal**:
```
Slashing + MEV alto → Grey Zone (QUEST detecta) → 
  stETH empieza a depeggear → Leverage positions get liquidated →
    Cascada de He et al. (16x amplificación)
```

QUEST es la señal de early warning que precede al fenómeno que He et al. documentan.

**Argumento crítico para el paper**: He et al. tienen la evidencia empírica de que las cascadas ocurren. QUEST propone el mecanismo de detección temprana. El backtest de mayo 2022 es la validación de esta cadena causal.

---

## Implicación directa para el backtest

Mayo 2022 (el stETH depeg) es el evento que He et al. usan implícitamente como validación de su modelo de cascadas. Si el backtest de QUEST muestra que GZS escaló **antes** del depeg, estamos aportando evidencia de que la señal macroprudencial hubiera funcionado.

→ Ver [[historical_dataset]] para la estrategia de datos

---

## Conexiones en vault

→ [[grey_zone_score]] — GZS como señal previa a las cascadas de He et al.
→ [[coordination_result]] — si agentes reducen exposure al GZS escalando, las cascadas no se forman
→ [[historical_dataset]] — mayo 2022 como caso de estudio compartido
