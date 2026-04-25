---
tags: [framework, capm, frontier]
tipo: teoría
estado: activo
---

# Frontera Eficiente CAPM-Style

Interpretación geométrica del [[utility_function|framework de utilidad]]. No es una afirmación de que el CAPM aplica a DeFi — es una herramienta visual para comunicar el mecanismo.

---

## La ecuación

$$E(R_a) = R_f + \beta_{GZS} \cdot (E(R_m) - R_f)$$

| Término | Significado en QUEST |
|---------|---------------------|
| $R_f$ | Yield base de staking ETH (CL issuance) — la "tasa libre de riesgo" de la economía Ethereum |
| $\beta_{GZS}$ | Coeficiente de exposición sistémica del agente = [[exposure_ratio\|α]] × β_max |
| $E(R_m)$ | Retorno de mercado DeFi agregado |

**Nota importante**: $\beta_{GZS}$ es un **parámetro de diseño** derivado de la exposición elegida por el agente — no es una covarianza estadística estimada de datos históricos. El framing CAPM se usa por su intuición geométrica, no como claim empírico.

---

## El mecanismo geométrico

En espacio $(E(R), \sigma(GZS))$:

**GZS = HEALTHY**: La Capital Market Line (CML) tiene pendiente pronunciada — alto retorno por unidad de riesgo. Los agentes racionalmente concentran en posiciones LST-colateralizadas.

**GZS = GREY_ZONE**: La frontera eficiente se **desplaza a la izquierda**. Las mismas estrategias ahora cargan mayor varianza sistémica. Los agentes racionales migran hacia posiciones de menor $\beta_{GZS}$.

**GZS = CRITICAL**: La CML casi colapsa. La única posición en la frontera eficiente es cero exposición LST.

---

## Las curvas de indiferencia

Locus de estrategias con utilidad constante $U = U_0$:

$$E(R) = U_0 + \frac{\lambda}{2}\sigma^2(GZS)$$

Son parábolas en $\sigma$. A medida que GZS sube, el agente necesita mayor $E(R)$ para mantener la misma utilidad con la misma exposición — o debe reducir exposición para mantenerse en la misma curva de indiferencia.

---

## Por qué importa este framing

El paper de ethresear.ch usa este lenguaje porque la audiencia (investigadores, desarrolladores DeFi, EF) reconoce el CAPM. Permite conectar QUEST con la teoría de portafolios sin inventar vocabulario nuevo.

→ Ver el paper completo: [[ethresear_v2]]
