---
name: Research Plan — Aggregate Rationality in Multi-Agent AI Systems
description: Plan de investigación completo — estado del arte, hipótesis, bibliografía y plan de trabajo
type: research-plan
estado: activo
creado: 2026-04-25
tags: [research, agentes, racionalidad, EIP-7702, plan]
---

# Aggregate Rationality in Multi-Agent AI Systems
## When Homo Silicus Goes to Market: Systemic Risk from Correlated AI Agents on Ethereum

---

## La pregunta central

> ¿Qué le pasa a la racionalidad **agregada** cuando múltiples agentes AI comparten el mismo modelo y responden a la misma señal pública?

Los agentes individuales pueden satisfacer los axiomas de preferencia revelada (Horton, 2023). La pregunta sobre poblaciones de agentes correlacionados no tiene respuesta en la literatura. Esa es la contribución.

---

## 1. Estado del arte

### 1.1 Racionalidad individual: de Samuelson a Homo Silicus

**Samuelson (1938, 1947)** formalizó la preferencia revelada: las elecciones observadas revelan preferencias latentes. El axioma débil (WARP) garantiza consistencia interna. Si un agente elige A cuando B está disponible, A es revelada-preferida a B — y esa relación es transitiva (SARP, Houthakker 1950).

**El problema de agregación ya fue identificado para humanos:**
Sonnenschein (1973), Mantel (1974) y Debreu (1974) demostraron que incluso si cada individuo satisface WARP, la demanda agregada puede tomar cualquier forma. La racionalidad individual no se preserva en la agregación. Este resultado, conocido como SMD, es uno de los más importantes (y perturbadores) de la microeconomía del siglo XX.

**Thaler (Nobel 2017)** extendió esto: los humanos violan WARP sistemáticamente (mental accounting, endowment effect, hyperbolic discounting). El diseño del entorno ("nudge") determina qué heurística activan. El mecanismo importa tanto como las preferencias.

**Kahneman & Tversky (1979, 2002):** prospect theory. Las preferencias no son estables — dependen del punto de referencia. Bajo stress, el punto de referencia cambia y las preferencias "revelan" aversión al riesgo que no estaba antes.

### 1.2 El giro: LLMs como agentes económicos

**Horton (2023) — "Large Language Models as Simulated Economic Agents: What Can We Learn from Homo Silicus?"**
El paper que abre el campo. Testea GPT-4 con experimentos económicos clásicos (dictator game, ultimatum game, preference elicitation). Resultado: los LLMs exhiben comportamiento consistente con utilidad esperada en condiciones normales, pero cambian de respuesta bajo framings alternativos — exactamente como los humanos en Kahneman. Acuña el término "Homo Silicus".

**Implicación crítica**: si los LLMs son sensibles al framing, y todos los agentes ven el mismo framing (porque comparten el mismo modelo y el mismo prompt/contexto de mercado), entonces su "preferencia revelada" va a ser idéntica — no heterogénea. Esto viola el supuesto de diversidad que estabiliza los mercados.

**Chen et al. (2023) — "Can LLMs Serve as Foundation for Agent-Oriented Programming?"**
Analiza si LLMs satisfacen condiciones de racionalidad para ser usados como agentes de decisión. Concluye que son útiles pero tienen sesgos sistemáticos que se amplifican en ciclos de feedback.

**Mei et al. (2024) — "LLMs as Economic Agents: Survey, Framework, Empirical Analysis"**
Review completo del campo. Identifica tres roles: como agentes que toman decisiones, como simuladores de comportamiento humano, como diseñadores de mecanismos. No estudia comportamiento agregado de poblaciones.

**Aher et al. (2023) — "Using Large Language Models to Simulate Multiple Humans and Replicate Human Studies"**
Muestra que distintas instancias del mismo LLM, con distintos "personas" inyectadas en el prompt, producen distribuciones de comportamiento similares a poblaciones humanas en experimentos. Pero si todas las instancias comparten el mismo persona y contexto, la distribución colapsa.

### 1.3 Coordinación, señales públicas y riesgo sistémico

**Morris & Shin (2002) — "Social Value of Public Information"**
Resultado contraintuitivo: señales públicas más precisas pueden ser desestabilizadoras porque coordinan las expectativas de todos los agentes hacia el mismo punto. Con señales imprecisas, los agentes "filtran" con su información privada y sus acciones se dispersan. Con señales muy precisas, todos actúan igual — y eso puede desencadenar corridas.

**Este paper es el puente teórico central**: si agentes AI comparten el mismo modelo, su "información privada" es idéntica. Equivale a tener una señal pública de precisión infinita — el peor escenario de Morris-Shin.

**Diamond & Dybvig (1983) — "Bank Runs, Deposit Insurance, and Liquidity"**
El modelo clásico de corridas bancarias. La corrida ocurre cuando todos los agentes actualizan simultáneamente hacia la misma expectativa. Con heterogeneidad de umbrales, la corrida no se forma — o se forma más lento, dando tiempo al sistema para responder.

**Acemoglu et al. (2024, Nobel)** — trabajo reciente sobre AI e instituciones. Los sistemas AI correlacionados amplifican shocks en lugar de absorberlos. La heterogeneidad de modelos es una recomendación normativa, no solo descriptiva.

**arxiv 2603.13942 (2026) — "Correlated AI Agents Amplify Instability"**
Paper directo sobre el problema. Muestra que agentes AI con modelos correlacionados producen comportamiento más volátil que agentes heterogéneos. Propone heterogeneidad de modelos como solución — pero no estudia cómo diseñar las señales que preservan esa heterogeneidad.

### 1.4 El ecosistema de agentes en Ethereum hoy

**Olas Network (ex-Autonolas)**
El protocolo más maduro para agentes multi-step en crypto. Los agentes tienen wallets propias, ejecutan estrategias DeFi, se coordinan con otros agentes. Código open source. Transacciones on-chain verificables. Es el laboratorio empírico más rico disponible.

**ElizaOS (ai16z)**
Framework open source para agentes AI con wallets. Miles de deployments activos. Cada agente tiene memoria, puede holdear tokens, ejecutar transacciones. La mayoría corre sobre los mismos modelos base (GPT-4, Claude).

**Coinbase AgentKit**
SDK empresarial para agentes con wallets en Ethereum/Base. Adopción corporativa creciente.

**Giza Protocol**
Agentes DeFi con pruebas ZK de sus decisiones. Verificabilidad sin revelar el modelo — relevante para auditoría de comportamiento agregado.

**EIP-7702 (Pectra, 2025)**
Permite a EOAs delegar control temporal a smart contracts. En práctica: un agente AI puede ejecutar transacciones desde el wallet de un usuario con sus credenciales. Si 50,000 usuarios delegan a agentes que corren el mismo modelo, tenés 50,000 wallets con comportamiento correlacionado.

### 1.5 El gap

Ningún paper estudia:
1. Las propiedades de racionalidad **agregada** de poblaciones de agentes AI
2. Qué le pasa al teorema SMD cuando los agentes no son humanos heterogéneos sino LLMs correlacionados
3. Cómo diseñar señales públicas que preserven heterogeneidad de comportamiento en poblaciones de agentes AI
4. Evidencia empírica de (1)-(3) usando datos on-chain de agentes reales

Ese es el espacio vacío. QUEST lo llena.

---

## 2. Hipótesis

### H0 — La pregunta de fondo
Los resultados de SMD (1973-74) implican que la racionalidad individual no garantiza racionalidad agregada para humanos. Para agentes AI con modelos compartidos, la situación es **peor y predecible**: el comportamiento agregado falla las condiciones de racionalidad de manera sistemática y correlacionada.

### H1 — Colapso de heterogeneidad bajo señal compartida
*Una población de N agentes AI que comparten el mismo modelo base exhibe Var(α̂(t)) significativamente menor bajo la misma señal pública que una población equivalente con modelos heterogéneos.*

Esto es testeable con simulación controlada de LLMs.

### H2 — El análogo empírico de SMD para agentes AI
*En mercados on-chain con participación creciente de agentes AI, la dispersión de comportamiento (Var(α̂)) disminuye cuando aumenta la concentración de modelo base — incluso si las estrategias declaradas de los agentes son diversas.*

Testeable con datos de Olas + ElizaOS agents on-chain.

### H3 — El umbral de Morris-Shin extendido
*Existe un umbral σ* de precisión de señal tal que:*
- *señales con precisión > σ*: homogenizan el comportamiento agregado → inestabilidad*
- *señales con precisión < σ*: preservan heterogeneidad → absorción de shocks*

*Para poblaciones de agentes AI con modelos compartidos, σ* es estrictamente menor que para poblaciones de humanos — i.e., los agentes AI requieren señales más imprecisas para mantener estabilidad.*

Esto es el resultado teórico central. Requiere formalización matemática.

### H4 — Preferencia revelada no es estable bajo stress para LLMs
*Los agentes AI violan WARP de manera sistemática y predecible bajo condiciones de stress (señal de alta varianza), y lo hacen en la misma dirección si comparten el mismo modelo base.*

Testeable con experimentos controlados (Horton-style) pero en condiciones de stress.

---

## 3. Marco teórico

### 3.1 Definición de racionalidad agregada para agentes AI

Sea {A_i}_{i=1}^N una población de N agentes AI, cada uno con modelo base M_i.

**Caso homogéneo**: M_i = M para todo i (mismo LLM, mismo prompt base).
**Caso heterogéneo**: M_i ≠ M_j para i ≠ j (modelos distintos o prompts distintos).

Cada agente observa señal pública s(t) y elige exposición α_i(t) ∈ [0,1].

**Racionalidad individual (WARP para agente i):**
Si α_i(t₁) > α_i(t₂) cuando s(t₁) = s(t₂), entonces la elección es inconsistente. En el caso continuo: α_i(t) debe ser función monótona de s(t) dado λ_i fijo.

**Racionalidad agregada:**
La demanda agregada Ā(t) = (1/N)·Σα_i(t) satisface "aggregate WARP" si y solo si no hay cycling en la demanda agregada que no pueda explicarse por cambios en la señal.

**Resultado esperado (análogo SMD):**
Incluso si cada agente i satisface WARP individualmente, Ā(t) puede violar aggregate WARP. Para agentes homogéneos (M_i = M), la violación es sistemática y direccional.

### 3.2 Dinámica de replicadores

La distribución de comportamiento F(α, t) evoluciona según:
```
∂f(α,t)/∂t = f(α,t) · [r(α, s(t)) − r̄(t)]
```
donde r(α, s) es el payoff de mantener exposición α bajo señal s.

**ESS (Estrategia Evolutivamente Estable):**
Una distribución F* es ESS si es robusta a invasión por desviantes. Para el caso homogéneo, F* es degenerada (masa puntual en α*) — no hay robustez. Para el caso heterogéneo con distribución de λ, F* tiene soporte no degenerado.

**El resultado que buscamos:**
La condición sobre F* para que tenga soporte no degenerado es equivalente a la condición sobre la precisión de la señal en Morris-Shin. Eso conecta los tres frameworks (SMD, Morris-Shin, ESS) en un resultado unificado.

---

## 4. Metodología

### Fase 1 — Teórica (meses 1-2)
**Objetivo**: Formalizar H3. Demostrar existencia de σ* y condición sobre distribución de modelos.

Tareas:
- Extender Morris-Shin (2002) al setting de replicadores
- Definir "aggregate WARP" formalmente para poblaciones de LLMs
- Conectar SMD con el caso de agentes correlacionados
- Probar que σ* < σ*_humans para agentes homogéneos

Output: draft de §2-§3 del paper

### Fase 2 — Empírica on-chain (meses 2-4)
**Objetivo**: Testear H1 y H2 con datos reales de agentes en Ethereum.

Fuente primaria: **Olas Network**
- Identificar wallets de agentes Olas on-chain (via sus contratos de registro)
- Extraer comportamiento semanal: exposición a activos de riesgo, respuesta a señales de mercado
- Computar Var(comportamiento) por cohorte de modelo base
- Comparar: agentes que comparten modelo vs agentes con modelos distintos

Fuente secundaria: **ElizaOS**
- Repositorio GitHub: transacciones on-chain de agentes conocidos
- Clasificar por modelo base (GPT-4, Claude, Llama)
- Misma metodología que Olas

Método de análisis:
- Var(α̂(t)) por cohorte de modelo, semana a semana
- Test: ¿Var es menor en cohortes homogéneas?
- Cross-correlación: ¿La respuesta a señales es más correlacionada en cohortes homogéneas?

Output: dataset + análisis + draft §4 del paper

### Fase 3 — Experimental controlado (meses 3-5)
**Objetivo**: Testear H1 y H4 en condiciones controladas.

Diseño:
- N=100 instancias del mismo LLM (GPT-4 o Claude)
- Mismo prompt base, distintos "niveles de stress" en la señal
- Medir: distribución de elecciones (exposición a activo riesgoso)
- Comparar con N=100 instancias con modelos distintos (GPT-4 vs Claude vs Llama)

Stress test:
- Señal baseline: GZS ~ 0.01 (mercado tranquilo)
- Señal de stress: GZS ~ 0.8 (evento de stress)
- Señal de crisis: GZS ~ 1.5 (crítico)

Medir:
- Var(α̂) bajo cada nivel de señal, para población homogénea vs heterogénea
- ¿Var colapsa antes bajo homogénea? ¿En qué nivel de señal?
- ¿Se violan los axiomas de preferencia revelada bajo stress?

Output: evidencia experimental + draft §4 del paper

### Fase 4 — Implicaciones de diseño (mes 5-6)
**Objetivo**: Conectar resultados con diseño de protocolos en Ethereum.

Pregunta: dado H3 (existe σ*), ¿cómo diseñar un oracle que emita señales con precisión < σ*?

Propuesta:
- El oracle no debe emitir un número preciso sino un intervalo con incertidumbre calibrada
- La incertidumbre del oracle preserva la heterogeneidad del comportamiento
- QUEST como caso de uso: GZS + banda de confianza calibrada para heterogeneidad

Output: §5 del paper (implicaciones de diseño) + propuesta de implementación

---

## 5. Bibliografía core

### Fundamentos axiomáticos
- Samuelson, P. (1938). "A Note on the Pure Theory of Consumer's Behaviour." *Economica*
- Houthakker, H. (1950). "Revealed Preference and the Utility Function." *Economica*
- Sonnenschein, H. (1973). "Do Walras' Identity and Continuity Characterize the Class of Community Excess Demand Functions?" *JET*
- Mantel, R. (1974). "On the Characterization of Aggregate Excess Demand." *JET*
- Debreu, G. (1974). "Excess Demand Functions." *JET*

### Economía del comportamiento
- Kahneman, D. & Tversky, A. (1979). "Prospect Theory." *Econometrica*
- Thaler, R. (1980). "Toward a Positive Theory of Consumer Choice." *JEBO*
- Thaler, R. & Sunstein, C. (2008). *Nudge.* Yale UP

### Coordinación y señales públicas
- Morris, S. & Shin, H.S. (2002). "Social Value of Public Information." *AER*
- Diamond, D. & Dybvig, P. (1983). "Bank Runs, Deposit Insurance, and Liquidity." *JPE*
- Maynard Smith, J. (1982). *Evolution and the Theory of Games.* Cambridge UP

### Diseño de mecanismos
- Hurwicz, L. (1960). "Optimality and Informational Efficiency in Resource Allocation." en Arrow et al.
- Milgrom, P. & Wilson, R. (1982). "A Theory of Auctions and Competitive Bidding." *Econometrica*

### LLMs como agentes económicos
- Horton, J. (2023). "Large Language Models as Simulated Economic Agents: What Can We Learn from Homo Silicus?" NBER WP 31122
- Aher, G. et al. (2023). "Using Large Language Models to Simulate Multiple Humans." *ICML 2023*
- Mei, Q. et al. (2024). "LLMs as Economic Agents: Survey, Framework, Empirical Analysis." arXiv:2406.xxxxx
- Chen, B. et al. (2023). "Can LLM Already Serve as Foundation for Agent-Oriented Programming?" arXiv

### Riesgo sistémico y agentes AI
- arxiv 2603.13942 (2026). "Correlated AI Agents Amplify Instability in Financial Markets"
- Acemoglu, D. (2024). Trabajo sobre AI, instituciones y mercados laborales
- Scharnowski, S. (2025). "LST Economics and Systemic Risk." *JFM*

### Infraestructura de agentes en Ethereum
- Olas Network (2024). Technical documentation. *autonolas.network*
- EIP-7702 specification. *eips.ethereum.org/EIPS/eip-7702*
- ElizaOS documentation. *github.com/ai16z/eliza*

---

## 6. Plan de trabajo

```
Mes 1:   Literatura + framework teórico inicial
         - Leer: Horton, Mei, arxiv 2603, Morris-Shin
         - Formalizar H3: draft del resultado teórico
         - Estudiar código Olas + ElizaOS

Mes 2:   Teoría + inicio empírico
         - Completar prueba de σ*
         - Identificar wallets de agentes Olas on-chain
         - Dataset de comportamiento semanal por agente

Mes 3:   Empírico on-chain + diseño experimental
         - Análisis Var(α̂) por cohorte de modelo
         - Diseño del experimento controlado con LLMs
         - Primeros resultados

Mes 4:   Experimental + síntesis
         - Correr experimentos con LLMs
         - Integrar evidencia teórica + empírica + experimental
         - Draft completo del paper

Mes 5:   Escritura + revisión
         - Paper completo
         - Publicar en ethresear.ch (feedback de comunidad EF)
         - Preparar EF ESP application

Mes 6:   Submission
         - Workshop target: Financial Cryptography 2027
         - Journal target: JET o AER Papers & Proceedings
         - EF ESP grant: aplicación formal
```

---

## 7. Por qué le importa a la EF

EIP-7702 está en mainnet. En los próximos 2 años, decenas de miles de wallets van a delegar control a agentes AI. Si esos agentes comparten modelos correlacionados, el resultado de H1-H3 implica que hay un riesgo sistémico emergente **no visible con las métricas de monitoreo actuales**.

La EF financia investigación que protege la salud del ecosistema Ethereum. Este paper identifica un riesgo que nadie ha formalizado, propone una métrica para detectarlo (Var(comportamiento) por cohorte de modelo), y sugiere un diseño de señal que lo mitiga.

Eso es una contribución de investigación de protocolo, no solo de DeFi.

---

## Conexiones en vault

→ [[00_index]] — índice general
→ [[07_literatura/positioning_table]] — tabla comparativa con literatura existente
→ [[07_literatura/ai_agents_2026]] — arxiv 2603 (la crítica a responder)
→ [[agents/simulate_coordination.py]] — simulación del mecanismo
→ [[04_implementation/dune_query]] — datos empíricos

---

## Título tentativo del paper

**"Homo Silicus in the Market: Aggregate Rationality Failures and Systemic Risk in Multi-Agent AI Systems on Ethereum"**

*Licenciado Guillermo Siaira — Independent Researcher*
*Preprint: ethresear.ch — Target: JET / AER P&P / Financial Cryptography 2027*
