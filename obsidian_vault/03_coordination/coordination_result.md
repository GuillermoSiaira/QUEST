---
tags: [coordination, nash, game-theory]
tipo: teoría
estado: activo
---

# Resultado de Coordinación

El hallazgo teórico central de QUEST: en una economía de agentes QUEST-aware, la coordinación macroprudencial emerge como **equilibrio de Nash** de optimización individual — sin coerción, gobernanza ni comunicación entre agentes.

---

## Racionalidad individual (caso de un agente)

Un agente maximizando $U = E(R) - \frac{\lambda}{2}\sigma^2(\text{GZS})$ reducirá exposición a medida que GZS suba **por construcción**.

En el punto donde:
$$\frac{\lambda}{2}\sigma^2(\text{GZS}) \geq E(R)$$

La utilidad se vuelve no-positiva. La exposición óptima es cero. No se invoca ninguna regla externa.

**Esta es una tautología del diseño** — pero útil, porque elimina el problema de coordinación a nivel del agente individual.

---

## Sketch de Nash de 2 agentes (simétrico)

**Setup**: Dos agentes QUEST-aware $A, B$ con calibración idéntica $(\lambda, \sigma_{base}, k, E(R))$. GZS está por encima del umbral individual de cada uno.

**Acciones**: $s_i \in \{reduce, maintain\}$

**Payoffs**:
- $c$ = costo del yield foregone al reducir exposición (cierto, inmediato)
- $d$ = pérdida esperada por liquidación en cascada si al menos un agente mantiene exposición

**El supuesto clave**: por construcción de la función de utilidad con GZS sobre el umbral: $c < d$

**Argumento**:
- Si B reduce → A prefiere reducir (menor riesgo de cola, pierde poco yield)
- Si B mantiene → A aún prefiere reducir (evita liquidación en cascada)
- `reduce` es la **estrategia dominante** para cada agente independientemente de lo que haga el otro

**Conclusión**: $(\text{reduce}, \text{reduce})$ es el único equilibrio de Nash. Sobrevive eliminación iterada de estrategias dominadas.

---

## Qué dice y qué no dice este modelo

✅ **Establece**: la coordinación macroprudencial **no es inevitable que falle** en DeFi  
✅ **Establece**: es consecuencia de la señal ausente de las funciones de utilidad, no de una imposibilidad más profunda  
✅ **Establece**: en el modelo mínimo simétrico, emerge coordinación sin comunicación

❌ **No resuelve**: agentes con $\lambda$ heterogéneo  
❌ **No resuelve**: información parcial sobre el GZS real  
❌ **No resuelve**: dinámica de salidas correlacionadas con liquidez finita

→ Ver las limitaciones completas: [[free_rider_inversion]]
→ Ver las preguntas abiertas: [[open_questions]]
