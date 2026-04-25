---
tags: [program, research, academic]
tipo: programa
prioridad: 3
estado: esqueleto
fecha: 2026-04-24
---

# Programa de Investigación — De hallazgo a agenda

## Tesis

QUEST no es un paper único — es una **agenda de investigación** sobre cómo diseñar mecanismos económicos para agentes autónomos en sistemas financieros descentralizados. El draft actual de ethresear.ch es el artículo fundacional. Los siguientes son consecuencia.

---

## La agenda en 4 papers

### Paper 1 — El fundacional (escrito, listo)
**Título**: "Macroprudential Signals for Autonomous Agents: A Utility Framework for Systemic Risk Coordination in DeFi"

**Contribución**: muestra que la coordinación macroprudencial es posible sin coerción si los agentes codifican la señal en su utilidad.

**Status**: [[ethresear_v2|draft completo]]. Target: ethresear.ch → Barnabé Monnot.

---

### Paper 2 — El axiomático (próximo)
**Título tentativo**: "Rational Agents in Permissionless Finance: An Axiomatic Foundation for Utility Functions in DeFi"

**Contribución**: conectar formalmente los axiomas de Debreu-Arrow-Hahn con el diseño de funciones de utilidad para agentes DeFi. Argumentar por qué media-varianza con varianza exponencial en la señal es la elección canónica (teorema de representación específico para agentes autónomos en mercados stochastic con información pública).

**Status**: idea, no escrito.

**Gaps para escribir**:
1. Revisión literatura: ¿Hansen & Sargent tienen algo en "robust control" que ya diga esto?
2. Hay que distinguir claramente qué axioma justifica qué elección: ¿continuidad justifica exp()? ¿convexidad justifica el término cuadrático en σ? No es obvio.
3. Sin resultados de backtest, es filosofía. Con resultados, es ciencia.

---

### Paper 3 — El empírico
**Título tentativo**: "Backtesting Systemic Risk Signals: Historical Performance of QUEST-Aware Portfolios through LST Events (2022-2026)"

**Contribución**: evidencia empírica de que agentes que habrían consumido GZS durante Luna/UST, 3AC, FTX, y eventos menores de LST habrían tenido drawdowns significativamente menores.

**Status**: idea, **requiere dataset histórico**.

**Gaps para escribir**:
1. Reconstrucción histórica del GZS desde datos de Beacon/Execution 2020-presente.
2. Definir contrafactual: ¿qué habría hecho un agente con `λ = 0.6`? → backtest engine del [[program_technical]].
3. Este paper requiere que el Programa Técnico avance primero.

---

### Paper 4 — El mecanismo
**Título tentativo**: "Incentive-Compatible Certification of Utility Execution in Decentralized Agent Markets"

**Contribución**: mecanismo criptoeconómico por el cual agentes pueden probar verificablemente que ejecutaron su función de utilidad declarada, sin revelar información propietaria (parámetros exactos, tamaño del capital).

**Status**: idea. Es el paper más técnico-criptográfico.

**Gaps para escribir**:
1. ZK proofs de ejecución de funciones con exp() son no-triviales
2. AVS attestation es más realista pero menos elegante
3. Relación con ERC-8004 (reputation) tiene que ser explícita

---

## Literatura académica que hay que leer/citar

No podemos publicar esto con el nivel actual de referencias. Cinco lecturas obligatorias antes de escribir el Paper 2:

| Referencia | Por qué importa |
|-----------|-----------------|
| Debreu (1954), "Representation of a Preference Ordering by a Numerical Function" | El teorema de representación base |
| Hansen & Sargent (2008), "Robustness" | Decisión bajo incertidumbre — conecta con σ²(GZS) como medida de Knightian uncertainty |
| Markowitz (1952), "Portfolio Selection" | La función U media-varianza canónica |
| Arrow (1964), "The Role of Securities in the Optimal Allocation of Risk-Bearing" | Mecanismos de completación de mercados → cómo una señal pública completa el mercado |
| Milgrom & Roberts (1990), "Rationalizability, Learning, and Equilibrium in Games with Strategic Complementarities" | El resultado de Nash en juegos donde los agentes se refuerzan mutuamente |

Para el Paper 4 (mecanismo criptográfico):
- Goldreich-Micali-Wigderson (1987) — ZK foundations
- Gluchowski et al. (2023) — ZK rollups y verificación de cómputo

---

## Publicaciones target

| Paper | Venue primario | Venue secundario |
|-------|---------------|------------------|
| Paper 1 | ethresear.ch | SSRN |
| Paper 2 | Journal of Financial Economics o JPE | arXiv + IC3 workshop |
| Paper 3 | Review of Financial Studies | DeFi Security Summit |
| Paper 4 | IACR ePrint / Financial Cryptography | Devcon talk |

---

## Gaps que bloquean este programa

1. **Dataset histórico** — bloquea Paper 3
2. **Lectura seria de la literatura académica** — bloquea Paper 2
3. **Colaborador académico** — probablemente necesitamos un co-autor con afiliación institucional para JFE. ¿Barnabé? ¿Tim Roughgarden? ¿Tarun Chitra?

---

## Próximas acciones concretas

- [ ] Publicar Paper 1 en ethresear.ch — 1 semana
- [ ] Leer Debreu (1954) y Hansen & Sargent capítulos 1-3 — 2 semanas
- [ ] Identificar colaborador académico potencial — mientras avanza lo anterior

→ Ver [[program_economic]] para quién paga la investigación
→ Ver [[program_technical]] para la infraestructura de backtest
