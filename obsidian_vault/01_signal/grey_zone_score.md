---
tags: [signal, gzs, formula]
tipo: señal
estado: produccion
---

# Grey Zone Score (GZS)

La señal macroprudencial central de QUEST. Mide la deuda de slashing oculta por rewards positivos.

Motivado por el gap estructural en [[safe_border_gap|safe_border.py de Lido]].

---

## Definición formal

$$\text{GZS}(e) = \frac{L_s}{R_{cl} + R_{el}}$$

| Variable | Significado |
|----------|-------------|
| $L_s$ | Gross slashing loss en epoch $e$ — `max(P_initial, P_midterm)` per Bellatrix spec |
| $R_{cl}$ | Consensus layer rewards en epoch $e$ (delta de balance entre todos los validadores) |
| $R_{el}$ | Proxy de actividad del execution layer — en v1, el EIP-1559 base fee burn |

---

## Cálculo de L_s

**Penalidad inicial (inmediata):**
$$P_{initial} = \frac{\text{effective\_balance}}{32}$$

**Penalidad midterm (proporcional, futura):**
$$P_{midterm} = \text{effective\_balance} \times \frac{3 \times \text{total\_slashed\_in\_window}}{\text{total\_active\_balance}}$$

`PROPORTIONAL_SLASHING_MULTIPLIER_BELLATRIX = 3` (consensus spec)

$$L_s = \max(P_{initial}, P_{midterm})$$

---

## Clasificación de riesgo

| GZS | Estado | Significado |
|-----|--------|-------------|
| < 0.5 | `HEALTHY` | Operación normal |
| 0.5 – 1.0 | `GREY_ZONE` | Slashing enmascarado por rewards; bypass de oracle posible |
| ≥ 1.0 | `CRITICAL` | Pérdidas exceden rewards totales |

---

## Propiedades de diseño

- **Epoch-sincronizado**: publicado cada ~384 segundos, alineado con el ritmo de la red
- **Escalar**: un número en [0, ∞), fácilmente consumible por agentes
- **Públicamente verificable**: todos los inputs vienen del Beacon REST API y Execution Layer

→ Ver cómo los agentes consumen esta señal: [[utility_function]]

---

## Limitaciones v1

- $R_{el}$ usa EIP-1559 burn como proxy del MEV. El ETH quemado no va a validadores — es una correlación, no una medición directa.
- Aggregado de red (no por protocolo). Lido domina hoy por peso en el TVL total.
- Operador centralizado (ECDSA, sin seguridad criptoeconómica). Phase 5: AVS con BLS multi-operador.

→ Ver debate completo: [[open_questions]]
