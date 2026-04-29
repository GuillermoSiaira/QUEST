---
tags: [framework, api, agent-design, consumer-theory]
tipo: hipótesis
estado: embrionario
fecha: 2026-04-24
---

# API de Funciones de Utilidad — La Extensión Natural

## La idea central

Los agentes DeFi autónomos necesitan funciones de utilidad. Hoy cada protocolo las hardcodea (o no las tiene). QUEST puede proveer una **API de funciones de utilidad calibradas** que otros agentes consuman como feature.

```
GET /api/utility?profile=conservative&gzs=0.7  →  { alpha: 0.35, utility: 0.0031 }
GET /api/utility?profile=moderate&gzs=0.7      →  { alpha: 0.52, utility: 0.0051 }
GET /api/utility?profile=aggressive&gzs=0.7    →  { alpha: 0.68, utility: 0.0063 }
GET /api/utility?lambda=0.9&sigma_base=0.04&k=2.303&gzs=0.7  →  { alpha: 0.28 }
```

El input es el GZS (señal de QUEST) + el perfil de riesgo del agente.
El output es la exposición óptima + utilidad resultante.

---

## Por qué la teoría del consumidor es la base correcta

Los **5 axiomas de preferencias racionales** (Debreu 1954, Arrow-Hahn 1971) son prescriptivos — no describen a humanos, describen a cualquier agente racional:

| Axioma | Implementación en U = E(R) − (λ/2)σ²(GZS) |
|--------|---------------------------------------------|
| **Completitud** | El agente puede rankear cualquier par de estrategias por su utilidad escalar |
| **Transitividad** | Si U(A) > U(B) y U(B) > U(C) → U(A) > U(C) — la función escalar garantiza esto |
| **Continuidad** | U es continua en GZS por construcción (exponencial diferenciable) |
| **Monotonicidad** | ∂U/∂E(R) > 0 — siempre preferir más retorno, dado el mismo riesgo |
| **Convexidad** | ∂²U/∂α² < 0 — preferir diversificación sobre concentración extrema |

**El gap en DeFi**: en TradFi, las funciones de utilidad se *estiman* de preferencias reveladas. En DeFi, con agentes autónomos, se *diseñan* en tiempo de construcción. QUEST propone estandarizar ese diseño.

---

## La analogía con SOFR / Fed Funds Rate

En TradFi:
- La Fed publica la Fed Funds Rate (señal de referencia, política monetaria)
- Cada institución aplica su propio spread/modelo de riesgo encima
- El sistema financiero coordina implícitamente alrededor de esa señal

Con QUEST:
- QUEST publica el GZS cada epoch (señal de riesgo sistémico)
- La API de utilidad provee el "spread layer" — la función de conversión señal → acción
- Los agentes DeFi coordinan implícitamente alrededor del GZS

**El GZS es la "tasa de riesgo sistémico de referencia" de Ethereum.**

---

## Perfiles de calibración propuestos

| Perfil | λ | σ_base | Descripción |
|--------|---|--------|-------------|
| `conservative` | 1.2 | 0.07 | Fondos de tesorería DAO, liquidez crítica |
| `moderate` | 0.6 | 0.05 | Referencia del paper — vault DeFi estándar |
| `aggressive` | 0.3 | 0.03 | Estrategias de alto rendimiento, capital especulativo |
| `custom` | params | params | Agente provee sus propios parámetros |

---

## Implicaciones para la arquitectura QUEST

```
QUEST hoy:          GZS escalar → on-chain → agentes lo leen directo

QUEST con API:      GZS escalar → API de utilidad → exposure target → agentes
                                       ↑
                              library de perfiles calibrados
                              (conservative / moderate / aggressive / custom)
```

---

## Por qué esto es granteable

1. **EigenLayer**: Los AVS operators necesitan funciones de utilidad para gestionar su riesgo de slashing. QUEST les provee la infraestructura.

2. **Ethereum Foundation (ESP)**: "Estandarización del espacio de diseño de funciones de utilidad para agentes autónomos en DeFi" — es investigación de mecanismos aplicada.

3. **Potencial ERC**: Un estándar para que agentes declaren su perfil de utilidad on-chain — composable con ERC-8004 (reputación de agentes).

---

## Preguntas abiertas específicas

- ¿Cómo se certifica que un agente está usando la función de utilidad que declara? (problema de verificabilidad)
- ¿Deberían los perfiles ser immutables en deployment o actualizables por governance?
- ¿Hay un argumento de mecanismo de diseño para la distribución óptima de perfiles en la población de agentes?

→ Ver [[open_questions]] para las preguntas del paper original
→ Ver [[utility_function]] para la formulación matemática base
→ Ver [[coordination_result]] para por qué esto produce coordinación
