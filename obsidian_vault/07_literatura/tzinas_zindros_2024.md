---
name: Tzinas & Zindros 2024 — Principal-Agent in Liquid Staking
description: El problema principal-agente en liquid staking — la fungibilidad del stake exacerba la desalineación validador-staker
type: literature
eprint: "2023/605"
publicado: Springer 2024 (Financial Cryptography)
autores: Apostolos Tzinas (NTUA), Dionysis Zindros (Stanford)
tags: [literatura, principal-agent, slashing, validadores, gobernanza, LST]
---

# Tzinas & Zindros (2024) — The Principal–Agent Problem in Liquid Staking

**eprint.iacr.org/2023/605** | Springer: [enlace](https://link.springer.com/chapter/10.1007/978-3-031-48806-1_29)

---

## Qué estudia

El problema fundamental de alineación de incentivos en liquid staking: cuando el stake es fungible (pooled), el staker (principal) no puede vincular su stake a un validador específico (agente). Esto exacerba el problema principal-agente clásico de la delegación.

---

## Problema que identifica

**La fungibilidad del stake destruye la representación proporcional:**

En staking directo: si tu validador es slasheado, tú sufres la pérdida.
En liquid staking: el slashing se distribuye a todos los stakers del pool, incluyendo a quienes eligieron validadores honestos.

Esto crea dos objetivos en tensión:
- **Representación proporcional**: cada staker debería ser afectado solo por su validador
- **Punición justa**: el staker solo debería sufrir pérdidas cuando su elección fue desinformada

**Son incompatibles en un pool fungible.**

---

## Solución propuesta

Identificación formal del dilema. Propuesta de mecanismo de punición proporcional que mitiga (no resuelve) la tensión. Demostración de un **ataque concreto** que explota la incompatibilidad.

No propone un oracle de riesgo sistémico ni ningún mecanismo de coordinación de agentes.

---

## Gap que QUEST llena

Tzinas & Zindros identifican que la desalineación principal-agente crea riesgo de slashing **distribuido** (no vinculado al validador que falló). QUEST detecta cuándo ese riesgo distribuido está siendo **enmascarado por recompensas MEV** — el momento donde el problema de Tzinas & Zindros se vuelve sistémico.

**La conexión**: el grey zone ocurre precisamente porque el slashing se distribuye silenciosamente en el pool mientras el oracle ve un rebase positivo. QUEST es el instrumento que haría visible ese proceso.

**Argumento**: el problema de alineación de Tzinas & Zindros es el mecanismo microeconómico que QUEST monitorea a nivel macro.

---

## Conexiones en vault

→ [[safe_border_gap]] — la distribución silenciosa es lo que el oracle de Lido no detecta
→ [[grey_zone_score]] — GZS como señal del momento en que la distribución se vuelve sistémica
→ [[free_rider_inversion]] — el problema de Tzinas es el free-rider que QUEST invierte
