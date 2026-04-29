---
tags: [framework, exposure, calibration]
tipo: derivación
estado: activo
---

# Ratio de Exposición (α)

La salida operacional del [[utility_function|framework de utilidad]]. Mapea el GZS a un target de exposición continuo en [0, 1].

---

## Definición

$$\alpha = \max\left(0,\ \frac{U}{E(R)}\right) = \max\left(0,\ 1 - \frac{\lambda \cdot \sigma^2(\text{GZS})}{2 \cdot E(R)}\right)$$

Donde $\sigma^2(\text{GZS}) = \sigma_{base}^2 \cdot e^{k \cdot \text{GZS}}$

---

## Tabla de exposición (calibración de referencia)

Con $\sigma_{base} = 0.05$, $k = \ln 10$, $\lambda = 0.6$, $E(R) = 0.0075$:

| GZS | Exposición | Estado |
|-----|------------|--------|
| 0.0 | 90% | HEALTHY |
| 0.3 | ~81% | HEALTHY |
| 0.5 | ~68% | GREY_ZONE |
| 0.7 | ~50% | GREY_ZONE |
| 0.85 | ~25% | GREY_ZONE |
| 1.0 | 0% | CRITICAL |

---

## Observación clave

El punto de 50% de exposición cae en GZS ≈ 0.7, **no** en el punto medio 0.5. Esto es consecuencia de la forma exponencial — concentra la reducción donde el riesgo de cola es más alto.

La curva no es simétrica. En la región HEALTHY (0-0.5), la exposición cae gradualmente. En la región GREY_ZONE (0.5-1.0), la caída se acelera.

---

## Implementación on-chain

`QUESTAgent.sol` implementa este cálculo usando `PRBMath UD60x18.exp()` — aritmética de punto fijo para la función exponencial. La función de utilidad on-chain coincide exactamente con la especificación.

→ Ver el contrato: [[contracts]]

---

## Nota sobre calibración

Estos valores son ilustrativos, no empíricamente ajustados. La calibración óptima a través de una población heterogénea de agentes es una pregunta abierta.

→ Ver debate: [[open_questions#Q2 — Calibración]]
