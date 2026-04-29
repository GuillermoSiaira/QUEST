---
tags: [grant, paper, ethresear]
tipo: paper
estado: listo-para-publicar
version: v2 — 2026-04-24
target: ethresear.ch
---

# Macroprudential Signals for Autonomous Agents

**Paper completo**: ver `D:\projects\QUEST\grants\ethresear-v2.md`

Este nodo es el punto de entrada del vault al paper de ethresear.ch.

---

## Estructura del paper

| Sección | Contenido | Nodo vault |
|---------|-----------|------------|
| §1 El problema de coordinación | Por qué la gobernanza no alcanza | [[coordination_result]] |
| §2 El caso motivador | `safe_border.py` de Lido | [[safe_border_gap]] |
| §3 El Grey Zone Score | Definición formal, tabla de estados | [[grey_zone_score]] |
| §4 Framework de utilidad | Media-varianza con σ²(GZS) | [[utility_function]], [[exposure_ratio]], [[capm_frontier]] |
| §5 Resultado de coordinación | Dominancia + Nash sketch | [[coordination_result]], [[free_rider_inversion]] |
| §6 Preguntas abiertas | 5 preguntas para la comunidad | [[open_questions]] |
| §7 Implementación | Dashboard, API, QUESTAgent.sol | [[architecture]], [[contracts]] |

---

## Argumento en una línea

> Si los agentes DeFi codifican el GZS en su función de utilidad, reducir exposición durante estrés sistémico se vuelve **individualmente racional** — la coordinación macroprudencial emerge sin coerción.

---

## Estado de publicación

- [ ] Revisión final del draft
- [ ] Confirmar firma / afiliación
- [ ] Crear cuenta en ethresear.ch (si no existe)
- [ ] Publicar en categoría: Protocol Design / Economic Mechanisms
- [ ] Compartir con Barnabé Monnot (EF) post-publicación

---

## Destinatario objetivo

**Barnabé Monnot** (Economic Research, Ethereum Foundation) — trabaja en mecanismos económicos del protocolo. Es el evaluador más relevante para este trabajo.
