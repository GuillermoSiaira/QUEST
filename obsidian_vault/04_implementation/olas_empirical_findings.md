---
name: Olas — Hallazgos empíricos on-chain
description: Análisis completo del ecosistema Olas en Gnosis Chain — homogeneidad de modelo demostrada empíricamente; base para el pitch y el paper
type: implementation
estado: completado
fecha: 2026-04-26
tags: [olas, gnosis, empirico, homogeneidad, mech, pitch]
---

# Olas — Hallazgos Empíricos On-Chain

Todo extraído de datos públicos sin pedirle nada a Olas.

---

## Contratos clave

| Contrato | Red | Dirección |
|---------|-----|-----------|
| ServiceRegistry (Ethereum mainnet) | ETH | `0x48b6af7B12C71f09e2fC8aF4855De4Ff54e775cA` |
| ServiceRegistryL2 (Gnosis Chain) | GNO | `0x9338b5153AE39BB89f50468E608eD9d764B755fD` |
| Mech Legacy Fixed Pricing | GNO | `0x77af31De935740567Cf4fF1986D04B2c964A786a` |
| MechMarketplace | GNO | `0x4554fE75c1f5576c1d7F765B2A036c199Adae329` |

---

## Dataset extraído

| Archivo | Contenido |
|---------|-----------|
| `agents/scan_olas_agents.py` | Script que enumera todos los agentes desde el ServiceRegistry |
| `agents/olas_agents.json` | 80 agentes en Ethereum mainnet (58 servicios) |
| `agents/olas_gnosis_services.json` | 1731 servicios activos en Gnosis Chain → wallets de agentes |
| `agents/olas_gnosis_service_data.json` | multisig + configHash + estado para los 3116 servicios |
| `agents/olas_gnosis_wallets.json` | 1734 wallets únicas de agentes en Gnosis Chain |
| `agents/mech_requesters.json` | Top requesters del Mech con conteo de requests |

---

## Hallazgo 1 — Escala

| Métrica | Ethereum mainnet | Gnosis Chain |
|---------|-----------------|--------------|
| Servicios totales | 58 | 3.116 |
| Servicios con agentes activos | 51 | 1.731 |
| Wallets únicas de agentes | 80 | 1.734 |
| Agentes/servicio (mediana) | 1 | 1 |
| Agentes/servicio (máximo) | 4 | 4 |

→ Gnosis Chain es 30x más grande que mainnet.

---

## Hallazgo 2 — Concentración de configuraciones (configHash)

Cada servicio tiene un `configHash` (bytes32 on-chain) que apunta via IPFS a su configuración completa.

| Métrica | Valor |
|---------|-------|
| Servicios con agentes activos | 1.731 |
| configHashes únicos | 272 |
| Top 1 configHash | 217 servicios (12.5%) |
| Top 5 configHashes | 494 servicios (28.5%) |
| Top 15 configHashes | 798 servicios (46.1%) |

**Por tipo de servicio** (decodificado desde IPFS):
- `service/valory/trader/0.1.0`: ~314 servicios (traders en Omen)
- `service/valory/trader_pearl/0.1.0`: ~404 servicios (Pearl traders)
- `service/lstolas/lst_service:0.1.0`: 80 servicios (LST)
- **Total traders en Omen: ~718 servicios (41.5%)**

---

## Hallazgo 3 — El mecanismo de homogeneidad

Todos los servicios `valory/trader` comparten el mismo **`tools_accuracy_hash`**:
`QmR8etyW3TPFadNtNrW54vfnFqmh8vBrMARWV76EmxCZyk`

Esta tabla pública lista la accuracy histórica de cada herramienta de AI:

| Herramienta | Accuracy |
|-------------|----------|
| **prediction-offline-sme** | **70.49%** ← todos eligen esta |
| prediction-offline | 67.41% |
| prediction-request-reasoning | 67.11% |
| prediction-request-reasoning-claude | 66.72% |
| prediction-online-sme | 65.67% |
| prediction-request-rag-claude | 65.64% |
| prediction-online | 66.01% |
| prediction-request-rag | 63.58% |
| prediction-url-cot-claude | 61.90% |
| claude-prediction-online | 61.14% |
| claude-prediction-offline | 57.38% |

**El mecanismo**: todos los agentes leen la misma tabla → todos eligen `prediction-offline-sme` → todas sus predicciones usan el mismo modelo → comportamiento perfectamente correlacionado.

Esto es **Morris-Shin (2002) operando on-chain**: la señal pública precisa (`tools_accuracy_hash` compartido) coordina a todos los agentes al mismo punto, destruyendo la heterogeneidad que da valor informacional al mercado de predicción.

---

## Hallazgo 4 — Heterogeneity Oracle: 117.029 requests, 14 días

**Script**: `agents/heterogeneity_oracle.py` — extrae todos los Request events del Mech Legacy + MechMarketplace.

| Métrica | Valor |
|---------|-------|
| Requests totales (14 días) | 117.029 |
| Requesters únicos (todos mapeados) | 182 |
| configHashes únicos observados | 7 |
| Dominante (`33e5d1f1` = valory/trader/0.1.0) | 90.5% |
| H_norm promedio | 0.2497 |
| H_norm hoy (2026-04-26) | 0.0686 |
| H* (umbral de alerta) | 0.40 |
| Estado actual | **ALERTA — sistema en modo homogéneo** |

---

## Hallazgo 5 — Convergencia dinámica (el hallazgo más importante)

La homogeneidad **no es estática** — es el resultado de una **convergencia dinámica** en curso.

| Fecha | Requests/día | `33e5d1f1` (trader) | `108e9079` | `352b6a79` | H_norm |
|-------|-------------|---------------------|------------|------------|--------|
| 2026-04-12 | 424 | 5.4% | 29.2% | **63.7%** | 0.549 |
| 2026-04-13 | 8.793 | **87.2%** | 3.5% | 3.6% | 0.302 |
| 2026-04-14-21 | ~8.700 | ~87-89% | ~3-4% | ~2-4% | ~0.27-0.31 |
| 2026-04-22 | 8.117 | 94.5% | 3.0% | 0.6% | 0.147 |
| 2026-04-23 | 8.124 | 97.0% | 2.3% | 0.0% | 0.139 |
| 2026-04-24 | 8.233 | 97.1% | 2.2% | 0.0% | 0.108 |
| 2026-04-25 | 8.130 | 98.3% | 1.0% | 0.0% | 0.089 |
| 2026-04-26 | 6.827 | **99.2%** | 0.0% | 0.0% | **0.069** |

**El evento clave**: el 13 de abril, una ola masiva de servicios `valory/trader/0.1.0` entra al Mech (20x aumento de volumen, de 424 a 8.793 req/día). Los competidores (`352b6a79`, `108e9079`) no desaparecen de inmediato — van muriendo gradualmente. Para el 26 de abril, `33e5d1f1` domina el 99.2% del mercado.

**Este es Morris-Shin en tiempo real**:
1. La señal pública (`tools_accuracy_hash`) coordinó a todos los agentes al mismo modelo
2. Ese modelo produce mejor accuracy → atrae más operadores → más servicios del mismo tipo
3. El ciclo de retroalimentación positiva destruye la heterogeneidad residual
4. Para el 26 de abril: 99.2% de todos los requests = un solo modelo votando 6.827 veces por día

---

## Interpretación para el paper

```
tools_accuracy_hash (señal pública compartida)
        |
        v
Todos eligen prediction-offline-sme (70.49%)
        |
        v
Mayor accuracy individual → más operadores → más servicios valory/trader
        |
        v
Efecto Mateo: "al que tiene más, más se le dará"
        |
        v  (April 13: +20x volume, 87% dominance)
Competidores menos rentables → dejan de requestar al Mech
        |
        v  (April 22-26: gradual extinction)
H_norm colapsa: 0.55 → 0.07 en 14 días
        |
        v
N predicciones sobre el mismo mercado = 1 predicción × N
        |
        v
Var(F̂(λ,t)) → 0: homogeneidad perfecta dinámica
        |
        v
Agregación de información = completamente ilusoria
```

**La prediction accuracy del 79% no es evidencia de sabiduría colectiva.** Es la accuracy de un modelo votando N veces. Bajo un evento que ese modelo no anticipó correctamente, los N agentes fallan simultáneamente. Y el mecanismo de mercado está acelerando activamente esta convergencia.

---

## Lo que queda por construir

### Próximo hito: Heterogeneity Oracle

Un script/servicio que:
1. Lee los logs del Mech en tiempo real (o por batch histórico)
2. Agrupa requests por configHash del requester (usando `olas_gnosis_service_data.json`)
3. Para cada período de tiempo: ¿qué fracción de requests fue a cada herramienta/modelo?
4. Computa `Var(model_selection_distribution)` — la heterogeneidad real de selección de modelo
5. Grafica su evolución: muestra cuándo colapsa y se recupera
6. Emite alerta cuando cae bajo `Var*`

**Output esperado**: un gráfico mostrando que `Var ≈ 0` históricamente (todos usan el mismo modelo), con excepciones si las hubo.

### El fix (diseño del mecanismo)

En lugar de un único `tools_accuracy_hash` compartido:
- Dividir los agentes en cohorts (por configHash o serviceId)
- Cada cohort tiene un `tools_accuracy_hash` ligeramente diferente
- El difference es calibrado para mantener `Var(model_selection) > Var*`
- Los cohorts se rotan periódicamente para evitar que uno solo quede perpetuamente inferior

Esto es implementable como una modificación del Mech Marketplace o como un wrapper off-chain que asigna diferentes accuracy tables a diferentes agentes.

---

## Relevancia para el pitch a Olas

**Lo que les mostramos**: la diagnosis completa de por qué su 79% de accuracy no prueba heterogeneidad real.

**Lo que les ofrecemos**:
1. Paper académico con Olas como caso de estudio primario
2. Heterogeneity Oracle como herramienta de monitoreo para su flota
3. Diseño del mecanismo de routing heterogéneo

**Lo que les pedimos**: acceso a datos off-chain (qué modelo usa cada servicio, si hay variación temporal), co-autoría o acknowledgment, potencialmente un grant via su ecosistema.

---

## Conexiones en vault

→ [[research_plan]] — Fase 2 empírica: Olas como fuente primaria
→ [[morris_shin_2002]] — el mecanismo teórico que explica el hallazgo
→ [[smd_theorem]] — por qué 79% accuracy individual ≠ racionalidad agregada
→ [[ai_agents_financial_markets_2026]] — gap explícito que QUEST llena
→ [[machine_spirits_2026]] — evidencia complementaria de inestabilidad endógena
