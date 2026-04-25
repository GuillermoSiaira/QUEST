---
name: Horton — Homo Silicus (2023)
description: LLMs como agentes económicos simulados — fundamento del concepto "Homo Silicus"; individual WARP satisfecho, gap colectivo abierto
type: literatura
estado: anotado
tags: [LLM, agentes, racionalidad, homo-silicus, behavioral-economics]
cita: "Horton, J.J., Filippas, A. & Manning, B.S. (2023). Large Language Models as Simulated Economic Agents: What Can We Learn from Homo Silicus? arXiv:2301.07543"
---

# Horton et al. (2023) — Homo Silicus

**arXiv**: 2301.07543 · **Publicado**: enero 2023, revisado feb 2026  
**Autores**: John J. Horton, Apostolos Filippas, Benjamin S. Manning  
**Journal**: NBER Working Paper

---

## Argumento central

Los LLMs pueden usarse como modelos computacionales del comportamiento económico humano — "Homo Silicus" en analogía con "Homo Economicus". Se les puede asignar dotaciones, información y preferencias para explorar resultados de comportamiento via simulación, de la misma manera que un economista usa un modelo teórico.

Los experimentos reproducen estudios clásicos (Charness & Rabin 2002, Kahneman et al. 1986). Los resultados son "cualitativamente similares" a los originales; las divergencias abren nuevas preguntas.

---

## Hallazgos clave

| Hallazgo | Implicación |
|----------|-------------|
| LLMs exhiben preferencias consistentes cuando se les asigna un rol económico | Satisfacen WARP individualmente |
| Resultados cualitativamente similares a humanos en dictator game, ultimatum | Capacidad de simulación confirmada |
| Divergencias del original = dato metodológico, no error | Permite comparación LLM vs. human |
| Sensibles a cómo se especifica el rol y las preferencias | El "prompt" opera como las preferencias en teoría del consumidor |

---

## Gap que QUEST puede llenar

Horton estudia **un** LLM simulando un humano. No estudia:
- ¿Qué pasa cuando N LLMs del mismo modelo actúan en mercado simultáneamente?
- ¿La "racionalidad individual" se preserva en el agregado?
- ¿Si todos tienen el mismo σ(latente), colapsan a las mismas decisiones?

→ Esta es exactamente la pregunta de **SMD** aplicada a Homo Silicus: la racionalidad individual no garantiza racionalidad agregada. QUEST operacionaliza el colapso.

---

## Conexión con nuestro trabajo

- Nombra el concepto que usamos: "Homo Silicus in the Market" es nuestra extensión directa
- La sensibilidad a especificación del rol → LLMs con mismo prompt base tienen λ implícito correlacionado → riesgo de homogeneización
- Su metodología (asignar preferencias vía prompt) es la base de nuestros experimentos de Fase 3

---

## Citas relevantes

> "We propose treating large language models as computational models of humans — Homo Silicus."

> "Results show qualitatively similar results to the original, with instances of divergence potentially offering new research directions."

---

## Conexiones en vault

→ [[research_plan]] — sección "Estado del Arte", referencia fundacional
→ [[aher_turing_2023]] — extensión: múltiples humanos simulados
→ [[utility_function]] — la función de utilidad es la especificación de preferencias del Homo Silicus
