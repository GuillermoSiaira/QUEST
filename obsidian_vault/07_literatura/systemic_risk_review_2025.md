---
name: Systemic Risk Review TradFi/DeFi 2025
description: Literatura review de riesgo sistémico micro y macro en TradFi y DeFi — 2021-2025, cubre Luna, Merge, FTX
type: literature
arxiv: 2508.12007
año: 2025
tags: [literatura, riesgo-sistemico, literatura-review, DeFi, TradFi, tail-risk, conectedness]
---

# Mapping Microscopic and Systemic Risks in TradFi and DeFi: A Literature Review (2025)

**arXiv: 2508.12007**

---

## Qué estudia

Literatura review comprehensiva de riesgos en TradFi y DeFi (2021-2025). Cubre múltiples shocks estructurales: colapso Terra-LUNA, Ethereum Merge, FTX, elección EE.UU. 2024.

---

## Problema que identifica

La topología de riesgo sistémico en crypto cambia con los eventos. Documenta:
- **Dependencia de DeFi en Ethereum** — tokens DeFi muestran dependencia creciente en ETH
- **Tail conectedness**: correlaciones aumentan en períodos de stress bajista
- **ETH como hub sistémico**: posición central de Ethereum y protocolos vinculados (UNI, etc.)

---

## Solución propuesta

Ninguna operacional. Es una literatura review — describe el estado del arte y mapea gaps.

---

## Gap que QUEST llena

El review documenta que **ETH es el hub sistémico** de DeFi y que la tail dependencia es alta en stress. QUEST es exactamente **el monitor de stress en el hub**: GZS mide la carga de slashing sobre el consensus layer de Ethereum — la capa de donde emana el riesgo sistémico documentado por esta literatura.

**Argumento de posicionamiento**: si el review dice que DeFi tiene alta dependencia en Ethereum y alta conectedness en stress, la pregunta natural es "¿qué detecta stress en Ethereum antes de que se propague?" QUEST es esa herramienta.

---

## Referencia metodológica

El paper usa partial correlation y información compartida para medir conectedness. Esto es relevante para la Q2 de QUEST (calibración): los métodos de este paper podrían usarse para calibrar empíricamente los parámetros de λ frente a datos históricos de conectedness.

---

## Conexiones en vault

→ [[grey_zone_score]] — stress en el consensus layer = lo que GZS mide
→ [[open_questions#Q2]] — métodos de calibración empírica de este paper son aplicables
