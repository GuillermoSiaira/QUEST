---
tags: [framework, utility, mean-variance]
tipo: teoría
estado: activo
---

# Función de Utilidad Media-Varianza

El corazón del framework de QUEST para agentes. Hace que reducir exposición en periodos de estrés sistémico sea **individualmente óptimo**, no solo colectivamente deseable.

---

## Formulación

$$U = E(R) - \frac{\lambda}{2} \cdot \sigma^2(\text{GZS})$$

| Término | Significado |
|---------|-------------|
| $E(R)$ | Retorno esperado (fees + yield) en el próximo epoch |
| $\lambda$ | Coeficiente de aversión al riesgo del agente (parámetro de diseño) |
| $\sigma^2(\text{GZS})$ | Varianza sistémica, parametrizada por la señal [[grey_zone_score\|GZS]] actual |

Tradición: Markowitz (1952) — media-varianza. El elemento no-estándar es $\sigma^2(\text{GZS})$: no es constante ni estimada de datos históricos. Es una función del GZS del epoch actual — una medida forward-looking y verificable del estrés sistémico.

---

## Por qué varianza exponencial

$$\sigma^2(\text{GZS}) = \sigma_{base}^2 \cdot e^{k \cdot \text{GZS}}$$

Una especificación lineal implicaría que cada unidad de GZS agrega varianza igual. Pero el riesgo sistémico no funciona así: cerca de GZS = 1.0, el ratio slashing/rewards se acerca a 1, significando que la capacidad del protocolo de absorber más slashings está casi agotada. Esto es un cambio de régimen, no una acumulación lineal.

La forma exponencial codifica esto: la varianza acelera a medida que GZS se acerca al umbral crítico, reflejando la estructura de riesgo de cola de las liquidaciones en cascada.

**Calibración de referencia**: $k = \ln(10)$, de modo que la varianza en GZS=1.0 es 10× la varianza en GZS=0.0.

---

## Calibración de referencia

| Parámetro | Valor | Racionale |
|-----------|-------|-----------|
| $\sigma_{base}$ | 0.05 | Volatilidad baseline de posiciones LST-colateralizadas |
| $k$ | ln(10) ≈ 2.303 | Varianza 10× en GZS=1.0 vs GZS=0.0 |
| $\lambda$ | 0.6 | Aversión al riesgo moderada |
| $E(R)$ | 0.0075 | = 10 · (λ/2) · σ_base² |

---

## Consecuencia directa

Un agente maximizando $U$ reducirá exposición a medida que GZS sube **por construcción**. En el punto donde $\frac{\lambda}{2}\sigma^2(\text{GZS}) \geq E(R)$, la utilidad se vuelve no-positiva y la exposición óptima es cero.

No se invoca ninguna regla externa. La función de utilidad del agente **es** la política.

→ Ver la exposición óptima calculada: [[exposure_ratio]]
→ Ver la interpretación geométrica: [[capm_frontier]]
→ Ver el resultado de coordinación: [[coordination_result]]
