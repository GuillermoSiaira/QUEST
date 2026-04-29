---
name: Gong (2026) — AI Agents in Financial Markets
description: Arquitectura AFMM; Prop. 1 heterogeneidad mejora price discovery; gap explícito sobre niveles óptimos de heterogeneidad — este gap es la contribución de QUEST
type: literatura
estado: anotado
tags: [AI-agents, finanzas, systemic-risk, heterogeneidad, AFMM]
cita: "Gong, H. (2026). AI Agents in Financial Markets: Architecture, Applications, and Systemic Implications. arXiv:2603.13942"
---

# Gong (2026) — AI Agents in Financial Markets

**arXiv**: 2603.13942 · **Año**: 2026  
**Autor**: Hui Gong

---

## Argumento central

Propone el Agentic Financial Market Model (AFMM): arquitectura de 4 capas para analizar cómo agentes AI autónomos afectan eficiencia de mercado y riesgo sistémico. La tesis central: "las implicaciones sistémicas dependen menos de la inteligencia del modelo que de cómo las arquitecturas de agentes están distribuidas, acopladas y gobernadas entre instituciones."

---

## Hallazgos clave

| Resultado | Implicación |
|-----------|-------------|
| **Model homogeneity = vulnerabilidad crítica** | Agentes con arquitectura similar fallan correlacionadamente |
| **Proposición 1**: heterogeneidad → mejor price discovery | Diversidad de agentes es estabilizadora |
| Gap explícito: niveles óptimos de heterogeneidad sin determinar | **Esta es nuestra contribución directa** |
| Equilibrio propuesto: "bounded autonomy" | Agentes como co-pilotos supervisados, no autónomos plenos |

---

## Por qué importa para QUEST

Este paper es la cita más directa del gap que llenamos:

> **"The open question remains: what are the optimal heterogeneity levels needed to prevent systemic instability while maintaining market efficiency?"**

La Proposición 1 dice que heterogeneidad es buena, pero **no dice cuánta** ni **cómo medirla**. QUEST propone:
- Medir: `Var(F̂(λ,t))` como proxy de heterogeneidad revelada
- Umbral: definir `Var*` debajo del cual el sistema es inestable (H3)
- Señal: GZS como indicador en tiempo real de cuándo el sistema se acerca al umbral

---

## Arquitectura AFMM (4 capas)

1. Percepción: sensores del entorno de mercado
2. Decisión: LLM o modelo de optimización
3. Ejecución: interfaz con mercado (wallets, órdenes)
4. Coordinación: protocolos multi-agente

→ QUEST opera principalmente en capa 3-4: coordinación sin coerción via señal pública.

---

## Citas relevantes

> "Systemic implications of AI in finance depend less on model intelligence alone than on how agent architectures are distributed, coupled, and governed across institutions."

> "Model homogeneity is the critical vulnerability — concentrated, similar agent designs present vulnerability points for financial stability."

---

## Conexiones en vault

→ [[research_plan]] — H3 (umbral σ*) responde exactamente al gap de Prop. 1
→ [[machine_spirits_2026]] — evidencia empírica de inestabilidad endógena con LLMs heterogéneos
→ [[grey_zone_score]] — GZS como señal de heterogeneidad en tiempo real
→ [[coordination_result]] — equilibrio Nash como formalización del bounded autonomy
