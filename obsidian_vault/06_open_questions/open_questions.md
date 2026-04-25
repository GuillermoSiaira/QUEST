---
tags: [open-questions, community, research]
tipo: agenda de investigación
estado: abierto
---

# Preguntas Abiertas

Las 5 preguntas genuinas que el paper de ethresear.ch dirige a la comunidad. No tenemos respuesta para estas — invitan colaboración.

---

## Q1 — Diseño de señal: ¿agregada o por protocolo?

GZS hoy es agregado (toda la red). Lido domina el total staked ETH, entonces el score agregado es esencialmente el score de Lido.

¿Debería ser por protocolo? Un score por-protocolo sería más preciso pero requiere resolver el problema de atribución de validadores para Rocket Pool, EtherFi, y otros.

**Relación con Fase 6**: → [[architecture]] → Fase 6

---

## Q2 — Calibración

Los parámetros de referencia ($\sigma_{base}$, $k$, $\lambda$) se eligieron analíticamente, no empíricamente.

- ¿Cuál es el método apropiado para calibrar la distribución de $\lambda$ en una población heterogénea de agentes?
- ¿Hay algún argumento de mecanismo de diseño para un $k$ canónico?

→ Ver parámetros de referencia: [[exposure_ratio]]

---

## Q3 — El proxy R_el

Usamos EIP-1559 burn como proxy de actividad MEV. El ETH quemado no va a validadores — la correlación es indirecta.

¿Cuál es el camino más limpio para obtener datos de MEV por epoch on-chain sin introducir un nuevo supuesto de confianza?

→ Ver limitaciones: [[grey_zone_score#Limitaciones v1]]

---

## Q4 — Validación histórica de umbrales

Los umbrales 0.5 y 1.0 están motivados analíticamente pero no validados contra eventos históricos de slashing.

¿Hay episodios históricos donde un GZS calibrado hubiera dado señal de alerta temprana?

→ Test histórico en producción: `risk-engine/test_historical_grey_zone.py`

---

## Q5 — Dinámica de salida

Si múltiples agentes QUEST-aware reducen exposición LST simultáneamente, el exit es epoch-sincronizado. Dependiendo de la liquidez disponible, esto podría **amplificar** en lugar de **amortiguar** la volatilidad.

¿Cuál es la condición sobre la distribución de $\lambda$ bajo la cual la reducción simultánea es estabilizadora?

Este es el punto más crítico para la solidez del [[coordination_result|resultado de coordinación]] a escala.

→ Ver la estructura del problema: [[free_rider_inversion#Limitaciones conocidas]]

---

## Estado

Estas preguntas se publican explícitamente en [[ethresear_v2|el paper de ethresear.ch]] para invitar respuestas de la comunidad.
