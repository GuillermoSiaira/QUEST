---
name: Jiang et al. (2025) — Rationality Survey (NAACL)
description: Survey NAACL 2025 sobre racionalidad en LLM agents — mapeo del estado del arte, identifica constraints y soluciones propuestas
type: literatura
estado: anotado
tags: [LLM, racionalidad, survey, NAACL2025, multi-agent]
cita: "Jiang, B. et al. (2025). Towards Rationality in Language and Multimodal Agents: A Survey. NAACL 2025. arXiv:2406.00252"
---

# Jiang et al. (2025) — Towards Rationality in LLM Agents (Survey)

**arXiv**: 2406.00252 · **Venue**: NAACL 2025 Main Conference  
**Autores**: Bowen Jiang, Yangxinyu Xie, Xiaomeng Wang, Yuan Yuan, et al.  
**Afiliación**: UPenn, MIT Lincoln Laboratory, et al.

---

## Argumento central

Survey sistemático sobre cómo construir agentes de lenguaje más racionales. Define racionalidad como "guiada por la razón, caracterizada por toma de decisiones alineada con evidencia y principios lógicos." Identifica constraints que impiden la racionalidad plena y los enfoques propuestos para superarlos.

---

## Constraints identificados

| Constraint | Descripción |
|------------|-------------|
| Bounded knowledge | El modelo tiene conocimiento limitado y puede hallucinar |
| Inconsistent outputs | La misma pregunta da respuestas diferentes en distintas sesiones |
| Context limitations | Ventana de contexto limita memoria de largo plazo |
| Affective biases | Sesgos en entrenamiento RLHF que distorsionan preferencias |

---

## Soluciones mapeadas

1. **Sistemas multi-agente y multimodales**: diversificación de agentes compensa bounded knowledge individual
2. **Herramientas externas y código**: ground truth computacional supera inconsistencia
3. **Razonamiento simbólico**: formalización reduce sesgos afectivos
4. **Funciones de utilidad**: operacionalizar preferencias reduce inconsistencia
5. **Conformal risk controls**: garantías probabilísticas de comportamiento

---

## Por qué importa para QUEST

Este survey **no cuestiona la racionalidad agregada** — asume que más racionalidad individual → más racionalidad del sistema. Ese es exactamente el gap que QUEST ataca vía SMD:

- El survey propone funciones de utilidad como solución a la inconsistencia
- QUEST muestra que uniformizar las funciones de utilidad (mismo λ) destruye estabilidad sistémica

Nuestro trabajo contradice la dirección principal del survey: más racionalidad individual homogénea **no** es la solución si el objetivo es estabilidad del sistema.

---

## Valor para el research plan

- Cita de estado del arte que establece dónde está el consenso que QUEST contradice
- La propuesta de "utility functions" como solución es exactamente lo que QUEST problematiza
- Confirma que el gap de racionalidad agregada no está abordado en la literatura actual

---

## Citas relevantes

> "Large language models frequently struggle with rationality due to constraints including bounded knowledge and inconsistent outputs."

> "The research community has responded by developing integrated systems combining multiple approaches rather than relying solely on individual models."

---

## Conexiones en vault

→ [[research_plan]] — H3/H4: la literatura actual no aborda racionalidad agregada
→ [[smd_theorem]] — base teórica por qué individual ≠ agregado
→ [[utility_function]] — funciones de utilidad como solución (que QUEST problematiza)
