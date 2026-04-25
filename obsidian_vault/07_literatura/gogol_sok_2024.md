---
name: Gogol SoK 2024 — LSTs and Restaking
description: Systematization of Knowledge de LSTs y restaking — marco técnico y económico comparativo de protocolos
type: literature
arxiv: 2404.00644
año: 2024
autores: Gogol, Velner et al.
tags: [literatura, LST, restaking, EigenLayer, sok, slashing, node-operators]
---

# Gogol et al. (2024) — SoK: Liquid Staking Tokens and Emerging Trends in Restaking

**arXiv: 2404.00644** | Semantic Scholar: [enlace](https://www.semanticscholar.org/paper/SoK:-Liquid-Staking-Tokens-(LSTs)-Gogol-Velner/f5051d96d5dfee169c5ddc9ac388a7620c423ec2)

---

## Qué estudia

Systematization of Knowledge (SoK) — revisión sistemática y framework unificado de:
- Modelos técnicos y económicos de protocolos de liquid staking
- Comparativa de node operator selection, distribución de rewards, y slashing
- Tendencias emergentes en restaking (EigenLayer, etc.)

---

## Problema que identifica

El ecosistema de LSTs y restaking carece de un framework unificado para comparar protocolos. Las diferencias en slashing, distribución de rewards, y selección de operadores crean riesgos heterogéneos que no están sistematizados.

---

## Solución propuesta

Framework comparativo sistemático. No propone mecanismos de coordinación ni oracles de riesgo. Es un paper de sistematización, no de solución.

**Áreas cubiertas:**
- Slashing en pools: qué pasa cuando un validator es slasheado en un pool de LST
- Node operator selection: modelos de selección y sus riesgos de concentración
- Restaking: cómo EigenLayer agrega capas de riesgo sobre el stake base

---

## Gap que QUEST llena

El SoK documenta **cómo funciona el slashing en pools** pero no aborda quién detecta el momento en que el slashing está siendo enmascarado por recompensas. QUEST cubre exactamente ese gap.

**Inserción especialmente relevante**: el SoK analiza restaking (EigenLayer) como tendencia emergente. QUEST corre **sobre EigenLayer** como AVS. Esta es la conexión más directa: QUEST es la capa de monitoreo macroprudencial que el SoK implícitamente requiere para que el restaking sea seguro.

**Argumento para el grant de EigenLayer**: el SoK documenta la necesidad; QUEST es la implementación.

---

## Conexiones en vault

→ [[architecture]] — AVS sobre EigenLayer
→ [[grey_zone_score]] — señal que falta en el SoK
→ [[grant_roadmap]] — EigenLayer grant directamente motivado por este gap
