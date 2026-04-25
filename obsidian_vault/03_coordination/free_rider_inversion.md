---
tags: [coordination, free-rider, mechanism-design]
tipo: teoría
estado: activo
---

# Inversión de la Estructura Free-Rider

La contribución conceptual de QUEST al problema de coordinación en DeFi.

---

## El problema clásico (TradFi)

En finanzas tradicionales, el free-rider en riesgo sistémico funciona así:

> Reducir exposición es **costoso para el individuo** pero **beneficioso para el sistema**.

Cada banco prefiere que *otros* reduzcan exposición primero. La racionalidad individual produce inacción colectiva. Por eso existe la regulación macroprudencial coercitiva — BASILEA, stress tests, requisitos de capital.

En DeFi, la coerción es inviable por diseño. El problema aparece irresoluble.

---

## La inversión con agentes QUEST-aware

Con la [[utility_function|función de utilidad parametrizada por GZS]], la estructura cambia:

> "Reducir exposición cuando GZS es alto" es la **estrategia dominante** — óptima independientemente de lo que hagan los otros agentes.

Ya no es una contribución al bien público que cada agente quisiera que otros hicieran. Es la acción que maximiza la utilidad individual **sin condicionarse al comportamiento ajeno**.

El bien sistémico emerge como subproducto de la optimización individual.

---

## La condición necesaria

Para que la inversión funcione, se requiere:

$$c < d$$

Donde:
- $c$ = yield foregone al reducir exposición (costo individual)
- $d$ = pérdida esperada de una liquidación en cascada (costo de no reducir)

Esto requiere $\lambda$ calibrado correctamente. Si $\lambda$ es demasiado bajo, el agente subestima la cola de riesgo y `maintain` puede dominar.

**La distribución de $\lambda$ en la población de agentes es el determinante crítico** de si el mecanismo funciona a escala.

---

## El rol de la señal

La inversión solo es posible si:
1. La señal ([[grey_zone_score|GZS]]) existe y es observable
2. Los agentes la incorporan en su función de utilidad en tiempo de diseño
3. La señal es epoch-sincronizada (reduce fricción de coordinación implícita)

QUEST provee el punto 1. El framework de utilidad es la propuesta para el punto 2. El punto 3 es consecuencia de la arquitectura.

---

## Limitaciones conocidas

**Heterogeneidad de λ**: Agentes con λ bajo pueden no reducir incluso cuando GZS es alto. Si son suficientemente grandes, pueden desestabilizar de todas formas.

**Dinámica de salida epoch-sincronizada**: Si muchos agentes reducen simultáneamente, el exit es sincronizado. Dependiendo de la liquidez disponible, esto podría **amplificar** la volatilidad en lugar de amortiguar.

→ Ver pregunta abierta específica: [[open_questions#Q5 — Dinámica de salida]]
