---
name: Li et al. (2024) — EconAgent
description: Agentes LLM con memoria y percepción reproducen Phillips Curve y Ley de Okun — valida LLMs como simuladores macroeconómicos
type: literatura
estado: anotado
tags: [LLM, macroeconomia, simulacion, ABM, ACL2024]
cita: "Li, N., Gao, C., Li, M., Li, Y. & Liao, Q. (2024). EconAgent: Large Language Model-Empowered Agents for Simulating Macroeconomic Activities. ACL 2024. arXiv:2310.10436"
---

# Li et al. (2024) — EconAgent

**arXiv**: 2310.10436 · **Venue**: ACL 2024  
**Autores**: Nian Li, Chen Gao, Mingyu Li, Yong Li, Qingmin Liao

---

## Argumento central

Combina LLMs con agent-based modeling (ABM) para simular actividad macroeconómica. Los agentes tienen módulos de percepción (genera heterogeneidad de decisiones) y memoria (refleja sobre experiencias pasadas y dinámicas de mercado). Resultado: fenómenos macroeconómicos emergentes realistas.

---

## Arquitectura EconAgent

| Módulo | Función |
|--------|---------|
| **Percepción** | Genera agentes con distintos mecanismos de decisión — fuente de heterogeneidad |
| **Memoria** | Permite reflexión sobre historia individual y dinámica de mercado |
| **Entorno** | Captura dinámicas de mercado emergentes de decisiones de trabajo y consumo |

---

## Hallazgos clave

- Reproduce **Curva de Phillips** (trade-off inflación-desempleo) como fenómeno emergente
- Reproduce **Ley de Okun** (relación output-desempleo) de manera endógena
- Supera a agentes rule-based y learning-based en fenómenos macroeconómicos
- Código público (GitHub): confirma reproducibilidad

---

## Por qué importa para QUEST

EconAgent demuestra que los LLMs **pueden producir racionalidad agregada** cuando se diseñan correctamente (módulo de percepción heterogéneo + memoria). Esto apoya nuestra tesis desde el lado positivo:

- Con heterogeneidad adecuada en F(λ) → fenómenos macroeconómicos estables emergen
- Sin heterogeneidad → el modelo colapsa a comportamientos uniformes

EconAgent es también una referencia metodológica para Fase 3 de nuestro research plan (simulación LLM experimental).

---

## Limitación para QUEST

EconAgent usa heterogeneidad **diseñada** (por el módulo de percepción). Nuestra pregunta es diferente: cuando los agentes son del mismo modelo base con el mismo prompt, ¿qué pasa con la heterogeneidad? EconAgent no responde eso.

---

## Citas relevantes

> "EconAgent enables heterogeneous agents with distinct decision-making mechanisms through a perception module."

> "EconAgent can make realistic decisions, leading to more reasonable macroeconomic phenomena compared to existing rule-based or learning-based agents."

---

## Conexiones en vault

→ [[research_plan]] — Fase 3 (simulación experimental): referencia metodológica
→ [[horton_homo_silicus_2023]] — LLMs individuales; EconAgent = escala a N agentes
→ [[coordination_result]] — coordinar sin coerción vs. coordinar vía memoria compartida
