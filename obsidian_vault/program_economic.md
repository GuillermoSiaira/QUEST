---
tags: [program, economic, mechanism-design]
tipo: programa
prioridad: 1
estado: desarrollo
fecha: 2026-04-24
---

# Programa Económico — ¿Quién es el cliente y qué vende QUEST?

## Tesis

QUEST no vende la función de utilidad. Vende **calibración curada + prueba de ejecución**. La función `U = E(R) − (λ/2)σ²(GZS)` es pública y replicable; lo que no es replicable es (a) saber qué λ funciona para qué tipo de agente bajo qué condiciones históricas, y (b) demostrar verificablemente que un agente respetó su calibración declarada.

---

## El cliente imaginario — ejercicio

Antes de seguir, hay que nombrar al cliente con cara y nombre. Tres candidatos:

### Cliente A — Fondos DeFi cuantitativos (Gauntlet-style)
- **Por qué les importaría**: ya gestionan parámetros de riesgo para Aave, Compound. Comprar un "modelo de riesgo sistémico pre-calibrado" ahorra research.
- **Qué pagarían**: API premium con calibraciones validadas backtest + SLA de uptime.
- **Tamaño**: ~50 firmas serias globalmente. Pagan $10K-$50K/mes por datos de riesgo.

### Cliente B — AVS operators de EigenLayer
- **Por qué les importaría**: su capital está en riesgo de slashing. Necesitan modelos de exposición, no tienen quants.
- **Qué pagarían**: integración on-chain donde el AVS consume GZS y ajusta automáticamente.
- **Tamaño**: ~500 operators activos hoy, creciendo. Menor willingness-to-pay individual pero mayor volumen.

### Cliente C — Protocolos LST-aware (vaults de Yearn, Morpho, Pendle)
- **Por qué les importaría**: cuando GZS sube, sus posiciones LST-colateralizadas están expuestas. Necesitan una señal estandarizada para incluir en sus propios oráculos.
- **Qué pagarían**: feed de datos (hot/warm storage) + derechos de citación.
- **Tamaño**: ~30 protocolos significativos.

**Pregunta crítica**: ¿cuál de los tres es el cliente real v1? No podemos construir para los tres simultáneamente. Hay que elegir.

Mi intuición es **Cliente B (AVS operators)** porque:
1. Es el único cliente donde el capital en riesgo justifica el costo
2. Conecta directamente con EigenLayer (grant-friendly)
3. El producto on-chain es más defensible que una API off-chain

Pero es discutible. Guillermo: ¿cuál es tu intuición?

---

## Qué vende QUEST, con precisión

| Producto | Replicable? | Precio indicativo |
|----------|-------------|-------------------|
| La fórmula U = E(R) − (λ/2)σ²(GZS) | Sí (10 líneas) | $0 — es pública |
| El cálculo en tiempo real del GZS | Costo medio (Beacon API, ~$500/mes infra) | Free tier |
| **Calibraciones validadas empíricamente** (λ, σ_base, k por tipo de agente, con backtest) | **No — requiere años de datos + investigación** | **$X/mes premium** |
| **Certificación on-chain de ejecución** (prueba ZK/AVS de que el agente usó la U declarada) | **No — requiere infraestructura criptográfica** | **Fee por certificación** |
| Reputación en ERC-8004 | No — es network effect | Implícito |

Los dos productos en negrita son el negocio. El resto es commodity o marketing.

---

## El mecanismo de adopción — por qué el primer adoptante gana

Este es el gap más crítico. Tiene que haber una razón por la cual un agente *temprano* gane algo por adoptar QUEST, independiente de si otros lo adoptan.

**Hipótesis 1 — Premium de reputación**: Los protocolos integrados con QUEST-aware agents les ofrecen mejores términos (menor collateral ratio, fee discount). Require que uno o dos protocolos grandes (Morpho? Aave?) acepten esta señal. **Costoso de conseguir pero con bola de nieve fuerte.**

**Hipótesis 2 — Auto-hedging superior**: Los backtest muestran que agentes QUEST-aware tienen mejor ratio de Sharpe durante eventos de estrés sistémico. Este es un argumento *puramente financiero* — no requiere que otros adopten. **Requiere backtest riguroso que todavía no tenemos.**

**Hipótesis 3 — Seguro de reputación post-evento**: Cuando ocurre el próximo "UST moment" en LST, los agentes que estaban QUEST-aware tienen prueba pública de haber reducido exposición. Esto es relevante para fiduciarios (fund managers con LPs). **Dependiente de timing — solo funciona después de un evento.**

La Hipótesis 2 es la más sólida porque no depende de adopción ajena ni de eventos futuros. Es la que hay que demostrar primero, con datos.

---

## Gaps que bloquean este programa

1. **Elegir el cliente v1** (A, B, o C) — decisión de producto
2. **Backtest histórico** del Sharpe ratio diferencial para agentes QUEST-aware vs. no-aware — requiere datos de eventos pasados (Luna/UST como proxy, aunque no es LST; pero también eventos menores: Lido en Mayo 2022, 3AC, etc.)
3. **Diseñar la prueba de ejecución** (ZK, AVS attestation, o simplemente firma off-chain): cuál es viable en v1

---

## Próximas acciones concretas — REORDENADAS

**La decisión del cliente v1 no se toma en el aire. Se descubre con dos señales:**

1. **Quién responde al paper** en ethresear.ch — los perfiles de los comentaristas son data sobre quién está pensando en este espacio
2. **Qué muestra el backtest** — si el backtest de Mayo 2022 muestra Sharpe diferencial grande para LSTs, el cliente natural son protocolos LST-aware. Si muestra mejor comportamiento para agentes apalancados, son fondos quant. Si muestra que los AVS operators hubieran sobrevivido mejor, son ellos.

**Entonces el orden real es**:

- [ ] **Publicar el paper en ethresear.ch** — 1 día, no requiere más trabajo teórico
- [ ] **Backtest de Mayo 2022 con Xatu** — 1 día, ahora factible (ver [[historical_dataset]])
- [ ] Con las dos señales anteriores, decidir cliente v1
- [ ] Entonces: diseñar arquitectura técnica enfocada a ese cliente

No al revés. No construir arquitectura sobre suposiciones.

→ Ver [[program_technical]] para la arquitectura que soporta esto
→ Ver [[program_research]] para el argumento académico
