---
tags: [grant, feedback, history]
tipo: registro
estado: activo
fecha: 2026-04-24
---

# Feedback Recibido — Registro Histórico

Para no repetir errores ni perder información valiosa de quienes evaluaron QUEST en versiones anteriores.

---

## Boris Stanic — Ethereum Foundation ESP (Lunes pre-pivote)

**Subject**: [QUEST] | ESP Office Hours
**De**: boris.stanic@ethereum.org

### Lo que dijo (textual)

> Regarding the "Existing Tooling for Ethereum Developers" wishlist item: that line refers to developer-facing tooling such as debuggers, profilers, testing frameworks, and fuzzers, not consensus-layer risk oracles. **QUEST does not fit that category.**

> On independent macroprudential monitoring of the Beacon chain: we reviewed your Strategic Grant Proposal on the EigenLayer forum to understand the full scope of QUEST and the Grey Zone framing. The risk surface you are describing **sits inside one specific staking protocol** rather than at the Ethereum protocol or infrastructure layer that ESP supports.

> We encourage you to engage both teams directly. **EigenLayer is the appropriate venue for an AVS** that certifies this kind of signal through restaked ETH. The cryptoeconomic security model and operator set you are designing belong inside that ecosystem. We also encourage you to **bring the Grey Zone framing to the Lido team** through their research forum. Since QUEST is built around Lido's oracle behavior and accounting model, it would benefit from engagement with the people closest to the protocol.

### Decodificación

| Lo que dijo | Lo que significa |
|-------------|------------------|
| "ESP wishlist es para debuggers/profilers/fuzzers" | QUEST nunca fue tooling para developers — el venue era equivocado |
| "Sits inside one specific staking protocol" | El framing era Lido-céntrico, no Ethereum-céntrico |
| "EigenLayer is the appropriate venue for an AVS" | Para infraestructura de certificación → EigenLayer |
| "Bring the Grey Zone framing to the Lido team" | Para gap específico de Lido → research forum de Lido |

### Comparativa: lo que se presentó vs. lo que ahora estamos haciendo

| Dimensión | **ESP (lo que vio Boris)** | **ethresear.ch v2 (post-pivote)** |
|-----------|---------------------------|-----------------------------------|
| Framing principal | Oracle macroprudencial / detector de bug | Framework de utilidad para agentes autónomos |
| Headline | "QUEST detecta blind spot en Lido" | "Coordinar riesgo sistémico sin coerción" |
| Tipo de contribución | Infraestructura / tooling | Teoría económica + implementación demo |
| Categoría reclamada | "Consensus Layer Tooling / Infrastructure" | Economics — mecanismo de incentivos |
| Aporte original | GZS + ERC-8033/8004 | `U = E(R) − (λ/2)σ²(GZS)` + Nash result |
| Lido en el pitch | Centro del pitch | Caso motivador en §2 (no la tesis) |
| Generalización | Específica de Lido | General desde el día uno |
| Venue target | EF ESP (grant) | ethresear.ch (paper público) |
| Budget pedido | $55K | $0 |
| Status | Rechazado | Listo para publicar |

### Plan de respuesta

**El feedback de Boris valida el pivote.** La crítica que él identificó (QUEST específico-Lido como tooling) está exactamente abordada por el framework actual (general, teoría de coordinación de agentes).

Tres movimientos secuenciales:

1. **Inmediato**: publicar paper en ethresear.ch (donde estamos)
2. **+1 semana**: respuesta corta a Boris reconociendo su feedback y compartiendo el paper
3. **+2 semanas**: con paper publicado, retomar EigenLayer (Phase 5 AVS) y Lido (per-protocol scores)

**No reaplicar a EF ESP ahora.** Mantenerlo en lista para 6-12 meses con paper publicado y posiblemente colaborador académico — ahí el framing es "research output sobre Ethereum economic security", no "Lido tooling".

### Draft de respuesta a Boris (post-publicación)

> Hi Boris,
>
> Thank you for the detailed feedback — it was useful in ways that go beyond a yes/no decision.
>
> Following your redirect, I re-framed the work around the broader question of how autonomous agents can coordinate around systemic risk without enforcement, motivated by the Lido oracle gap but not specific to it. The new piece is published on ethresear.ch:
>
> [link]
>
> The Grey Zone Score remains the concrete signal, but it now sits inside a utility-theoretic framework that I think is what was missing from the original ESP submission — the general claim, not just the specific tool.
>
> I'm engaging EigenLayer for the AVS layer (per your suggestion) and plan to bring the protocol-specific framing to Lido's research forum next.
>
> Thanks again for the redirect.
>
> Best,
> Guillermo

---

## Lido Bug Bounty — Pre-pivote

**Decisión**: clasificado como "research of interest" en lugar de vulnerabilidad explotable.

**Lo cual es correcto** — la Grey Zone es un gap estructural, no un zero-day. Su significancia es macroprudencial, no aguda.

Esta clasificación es la que abrió el camino al pivote: el bug solo no era suficiente para un grant tradicional, pero el framework teórico que lo generaliza sí puede serlo.

→ Esta caracterización está incluida explícitamente en §2 del [[ethresear_v2|paper]].

---

## Lecciones acumuladas

1. **QUEST no es tooling de Ethereum core** — fue un error tratar de venderlo como tal a EF ESP
2. **Lido específico ≠ propuesta general** — para venues como EF, hay que abstraer
3. **El framework teórico es el desbloqueador** — sin él, todo se ve como infrastructure work
4. **Los venues correctos son**:
   - ethresear.ch para teoría/research
   - EigenLayer para AVS infrastructure
   - Lido research forum para gap específico
   - EF ESP **eventualmente** con paper + colaborador académico
