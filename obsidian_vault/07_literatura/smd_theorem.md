---
name: SMD Theorem — Sonnenschein-Mantel-Debreu (1973-74)
description: La racionalidad individual no garantiza racionalidad agregada — fundamento teórico del gap que QUEST estudia en agentes AI
type: literatura
estado: anotado
tags: [teoria, SMD, racionalidad-agregada, micro-fundamentos, teoria-economica]
cita: "Sonnenschein, H. (1973). Do Walras' identity and continuity characterize the class of community excess demand functions? JET. Mantel, R. (1974). On the characterization of aggregate excess demand. JET. Debreu, G. (1974). Excess demand functions. JME."
---

# Teorema SMD — Sonnenschein-Mantel-Debreu

**Papers originales**:
- Sonnenschein, H. (1973). "Do Walras' identity and continuity characterize the class of community excess demand functions?" *Journal of Economic Theory*, 6(4), 345–354.
- Mantel, R. (1974). "On the characterization of aggregate excess demand." *Journal of Economic Theory*, 7(3), 348–353.
- Debreu, G. (1974). "Excess demand functions." *Journal of Mathematical Economics*, 1(1), 15–21.

---

## El resultado

**Enunciado informal**: si tienes N consumidores racionales (que satisfacen todas las condiciones neoclásicas: completitud, transitividad, continuidad, convexidad, monotonicidad), la **función de demanda agregada** puede ser prácticamente cualquier función continua que satisfaga la Ley de Walras.

**Enunciado formal**: Sea `z(p)` cualquier función continua de precios con `p·z(p) = 0` (Ley de Walras). Entonces existe una economía con consumidores racionales individuales cuya función de demanda agregada es exactamente `z(p)`.

---

## Implicaciones

| Resultado | Implicación |
|-----------|-------------|
| Racionalidad individual no restringe forma de z(p) | No se puede inferir racionalidad agregada de racionalidad individual |
| Múltiples equilibrios posibles | No hay garantía de equilibrio único o estable |
| Equilibrios inestables pueden ser consistentes con racionalidad individual | Micro-fundamentos neoclásicos no garantizan estabilidad macro |
| La distribución de F(λ) importa | El agregado depende de quién tiene cuánto y cuál es su λ |

---

## Por qué el SMD es más severo para LLMs

Para humanos, SMD dice: incluso con racionalidad individual, el agregado es arbitrario.

Para LLMs del mismo modelo, es **peor**:

1. Los humanos tienen preferencias heterogéneas por origen biológico, historia, cultura → F(λ) naturalmente dispersa
2. Los LLMs del mismo modelo tienen preferencias **correlacionadas** por diseño → F(λ) artificialmente concentrada
3. El SMD dice que con F(λ) concentrada, el comportamiento agregado puede ser patológico aunque cada agente sea perfectamente racional

→ **La racionalidad de los LLMs es su punto débil sistémico cuando son homogéneos.**

---

## Conexión con la tesis de QUEST

QUEST es esencialmente: el SMD aplicado a poblaciones de LLMs en DeFi.

```
SMD: racionalidad individual ≠ racionalidad agregada
QUEST: F(λ) dispersa → Var(F̂) > Var* → agregado racional en sentido sistémico
```

El GZS es el mecanismo que preserva F(λ) dispersa al dar información suficiente para que agentes con distintos λ tomen distintas decisiones (no colapsen a la misma acción).

---

## La paradoja de Horton

Horton (2023) demuestra que los LLMs satisfacen WARP individualmente → "Homo Silicus" es racional.  
SMD dice: eso no implica nada sobre el agregado.  
**QUEST cierra el círculo**: propone el mecanismo (F(λ) dispersa + señal GZS) que preserva racionalidad sistémica.

---

## Conexiones en vault

→ [[research_plan]] — fundamento teórico central de la investigación
→ [[horton_homo_silicus_2023]] — WARP individual demostrado; SMD = por qué eso no es suficiente
→ [[sparks_rationality_2026]] — evidencia reciente de racionalidad individual vs. agregada
→ [[coordination_result]] — equilibrio Nash que respeta SMD
→ [[utility_function]] — F(λ) como objeto que el SMD muestra que importa
