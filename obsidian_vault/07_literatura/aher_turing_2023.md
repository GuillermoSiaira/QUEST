---
name: Aher et al. — Turing Experiments (2023)
description: LLMs reproducen estudios de sujetos humanos; identifica "hyper-accuracy distortion" — LLMs sistemáticamente más precisos que humanos, lo que implica menos diversidad poblacional
type: literatura
estado: anotado
tags: [LLM, simulacion, diversidad, hyper-accuracy, ICML]
cita: "Aher, G., Arriaga, R.I. & Kalai, A.T. (2023). Using Large Language Models to Simulate Multiple Humans and Replicate Human Subject Studies. ICML 2023. arXiv:2208.10264"
---

# Aher et al. (2023) — Turing Experiments

**arXiv**: 2208.10264 · **Venue**: ICML 2023  
**Autores**: Gati Aher, Rosa I. Arriaga, Adam Tauman Kalai

---

## Argumento central

Introduce los "Turing Experiments" (TEs): evaluar si un LLM puede simular una muestra representativa de la población humana y reproducir estudios clásicos de comportamiento. A diferencia del Turing Test (¿puede un LLM pasar por un humano?), los TEs preguntan: ¿puede un LLM reproducir la distribución de respuestas de N humanos?

---

## Hallazgos clave

| Experimento | Resultado |
|-------------|-----------|
| Ultimatum Game | Reproducido exitosamente |
| Garden Path Sentences | Reproducido |
| Milgram Shock Experiment | Reproducido |
| **Wisdom of Crowds** | **Anomalía: hyper-accuracy distortion** |

### Hyper-accuracy distortion

En el experimento de Sabiduría de las Masas, los LLMs son **sistemáticamente más precisos** que los humanos. Esto tiene dos consecuencias:

1. **Menos ruido** en las estimaciones → menos diversidad de respuestas
2. **Convergencia artificial** a la respuesta "correcta" → si N agentes del mismo modelo responden, sus distribuciones se colapsan hacia el mismo punto

En términos de λ-heterogeneidad: si los LLMs tienen menos varianza en su percepción del riesgo, su F(λ) implícita es más estrecha que la humana. Una población de LLMs del mismo modelo es inherentemente más homogénea.

---

## Implicación para QUEST

La hyper-accuracy distortion **cuantifica** por qué los LLMs homogéneos son más peligrosos que los humanos homogéneos:

- Humanos tienen ruido idioscincratico → natural diversificación
- LLMs del mismo modelo tienen respuestas convergentes → riesgo de colapso de F(λ)

Esto conecta directamente con H1 de nuestro research plan: "agentes con λ homogéneo reducen Var(F̂) por debajo del umbral de estabilidad".

---

## Citas relevantes

> "The last TE reveals a 'hyper-accuracy distortion' present in some language models (including ChatGPT and GPT-4)."

> "This represents systematic overperformance on certain tasks that could impact educational and artistic applications."

---

## Conexiones en vault

→ [[research_plan]] — H1: λ homogéneo → Var baja → inestabilidad
→ [[horton_homo_silicus_2023]] — trabajo complementario en el mismo espacio
→ [[machine_spirits_2026]] — extensión: qué pasa cuando múltiples LLMs distintos interactúan
