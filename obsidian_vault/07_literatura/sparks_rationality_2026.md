---
name: Tak et al. (2026) — Sparks of Rationality
description: Reasoning LLMs satisfacen axiomas de racionalidad pero deliberación amplifica steering afectivo — trade-off racionalidad/manipulabilidad
type: literatura
estado: anotado
tags: [LLM, racionalidad, axiomas, reasoning, affective-steering]
cita: "Tak, A.N. et al. (2026). Sparks of Rationality: Do Reasoning LLMs Align with Human Judgment and Choice? arXiv:2601.22329"
---

# Tak et al. (2026) — Sparks of Rationality

**arXiv**: 2601.22329 · **Submittido**: enero 2026  
**Autores**: Ala N. Tak, Amin Banayeeanzade, et al.  
**Afiliación**: USC Information Sciences Institute + otros

---

## Argumento central

Evalúa si los LLMs de razonamiento (reasoning models) satisfacen los axiomas centrales de la teoría racional de elección. Resultado paradójico: la capacidad de razonamiento mejorada **aumenta** la racionalidad individual pero **amplifica** la vulnerabilidad a manipulación afectiva.

---

## Axiomas evaluados

| Axioma | Descripción |
|--------|-------------|
| Completitud | Para todo par (A,B): A≻B, B≻A, o A∼B |
| Transitividad | Si A≻B y B≻C entonces A≻C |
| Continuidad | Existen loterias que hacen al agente indiferente |
| Independencia | Axioma de von Neumann-Morgenstern (VNM) |

---

## Hallazgos clave

| Hallazgo | Implicación |
|----------|-------------|
| "Deliberate thinking reliably improves rationality" | Reasoning models más cercanos a maximización de valor esperado |
| "Amplifies sensitivity to affective interventions" | El mismo mecanismo que da racionalidad da manipulabilidad |
| In-context priming → extreme shifts | Fácil de manipular vía prompt |
| Representation-level steering → más human-like pero menos confiable | Trade-off fundamental |

---

## La paradoja para sistemas multi-agente

Si los reasoning models son más racionales individualmente → deberían satisfacer WARP → "Homo Silicus" mejorado.

Pero la amplificación afectiva implica: un prompt compartido puede **correlacionar** las respuestas de todos los agentes del mismo modelo. En mercado:
- Todos usan GPT-o3 o Claude o4
- Un evento sistémico activa "affective intervention" (pánico)
- Todos los agentes responden simultáneamente con el mismo sesgo

→ **El reasoning mejora la racionalidad individual pero empeora la racionalidad agregada** cuando el modelo es compartido.

Esta es H4 de nuestro research plan: "LLMs violan WARP sistemáticamente a nivel agregado aunque lo satisfagan individualmente."

---

## Citas relevantes

> "Deliberate 'thinking' reliably improves rationality and pushes models toward expected-value maximization."

> "The mechanisms enhancing rationality simultaneously amplify sensitivity to affective interventions."

---

## Conexiones en vault

→ [[research_plan]] — H4: individual WARP ok, agregado WARP violado
→ [[smd_theorem]] — teoría detrás de por qué individual ≠ agregado
→ [[aher_turing_2023]] — hyper-accuracy es otra manifestación del mismo problema
→ [[morris_shin_2002]] — señal pública precisa → correlaciona decisiones → inestabilidad
