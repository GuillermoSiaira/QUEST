---
tags: [implementation, data, backtest]
tipo: recurso
estado: verificado-parcial
fecha: 2026-04-24
actualizado: 2026-04-24 (post-probe)
---

# Dataset Histórico — Estrategia Multi-Fuente

> **Nota**: Inicialmente se pensó que Xatu cubría todo lo necesario. Un probe técnico del 2026-04-24 reveló que Xatu tiene slashings pero NO tiene balances de validators ni datos pre-Merge de execution layer. El backtest requiere 3 fuentes.

## Las 3 fuentes reales

| Componente GZS | Fuente | Costo | Status |
|----------------|--------|-------|--------|
| **Gross slashing loss** (numerador) | Xatu (EthPandaOps) parquet | $0 | ✅ verificado |
| **CL rewards** (denominador parte 1) | Beaconcha.in REST API | $0 (rate limited) | 🟡 accesible, rate-limit 1 req/s free tier |
| **EL burn / EIP-1559** (denominador parte 2) | Etherscan daily CSV o archive RPC | $0 | 🟡 no verificado |

## Xatu (slashings)

- **URL base**: `https://data.ethpandaops.io/xatu/mainnet/databases/default/{table}/YYYY/M/D.parquet`
- **Path format crítico**: sin zero-padding — `/2022/5/1.parquet` funciona, `/2022/05/01.parquet` da 404
- **Tablas relevantes (verificadas)**:
  - `canonical_beacon_block_proposer_slashing` (~8 KB/día)
  - `canonical_beacon_block_attester_slashing` (~9-21 KB/día)
  - `canonical_beacon_block` (~900 KB/día, metadata)
- **Tablas que NO existen en bucket público**:
  - `canonical_beacon_validators` ← crítico, bloquea CL rewards from Xatu
  - `canonical_execution_block` ← para pre-Merge no importa
- **Download total para mayo 2022**: ~28 MB. Trivial.

## Schema verificado de slashings

Slashings NO están embebidos en `canonical_beacon_block` como supuse originalmente. Están en tablas flat dedicadas, una fila por slashing.

Schema de `attester_slashing`:
```
attestation_1_attesting_indices: BIGINT[]
attestation_2_attesting_indices: BIGINT[]
```

Validadores slasheados = `list_intersect(attestation_1_attesting_indices, attestation_2_attesting_indices)`.

## Beaconcha.in (CL rewards)

- Endpoint: `/api/v1/validator/stats/{day}` (aggregate)
- Rate limit free: 1 req/s, 30K calls/mes (suficiente para mayo 2022: ~31 calls)
- Requiere parsear el campo aggregate de rewards diario

---

## Tablas relevantes para QUEST

| Tabla | Contenido | Uso en GZS |
|-------|-----------|-----------|
| `canonical_beacon_block` | Bloques con `proposer_slashings[]` y `attester_slashings[]` embebidos | Numerador: gross slashing loss |
| `canonical_beacon_validators` | Balance por validator por epoch | Denominador: CL rewards (delta de balance) |
| `canonical_beacon_validators_pubkeys` | Mapeo pubkey → withdrawal credentials | Atribución por protocolo (Lido, etc.) |
| `canonical_execution_block` | Base fee burn EIP-1559 (post-London, Ago 2021) | Denominador: R_el proxy |

---

## Eventos históricos target para backtest

Los eventos donde QUEST hubiera emitido señal relevante:

| Evento | Fecha | Por qué importa |
|--------|-------|-----------------|
| **stETH depeg** (Luna/UST + Celsius) | Mayo-Junio 2022 | stETH se despegó -7% del ETH; Lido no entró en bunker mode; pérdidas distribuidas sin señal |
| Celsius insolvencia | Junio 2022 | ~409K stETH en garantía; venta forzada presionó peg |
| FTX collapse | Nov 2022 | Menor impacto directo en staking pero estrés sistémico de mercado |
| Shapella upgrade | Abril 2023 | Habilitación de withdrawals — primer momento de "bunker mode posible" |
| Evento típico de slashing | varias fechas | Validar comportamiento en condiciones normales |

Mayo 2022 es el caso de estudio v1 porque:
- Es pre-Merge: R_cl existe, R_el burn existe, pero no hay MEV-Boost
- Es el único evento histórico donde claramente el "safe_border.py" habría fallado bajo el análisis actual
- Es un nombre reconocible para un paper empírico

---

## Complicación pre-Merge

Antes del Merge (15 Sep 2022), el CL y el EL eran cadenas separadas. Consecuencias para GZS histórico:

- **Pre-Merge** (Dec 2020 – Sep 2022): no hay MEV del CL, pero hay EIP-1559 burn desde Aug 2021. `R_el` se puede usar como proxy igual.
- **Post-Merge** (Sep 2022 – presente): arquitectura coincide con el GZS actual.

Esto significa que el backtest de Mayo 2022 va a dar un GZS con un denominador diferente conceptualmente. No es un problema — hay que documentarlo.

---

## Pasos concretos para el backtest

1. Instalar DuckDB: `pip install duckdb`
2. Query de prueba:
   ```python
   import duckdb
   conn = duckdb.connect()
   url = "https://data.ethpandaops.io/xatu/mainnet/databases/default/canonical_beacon_block/2022/5/10.parquet"
   result = conn.execute(f"""
     SELECT slot, proposer_index, 
            list_length(proposer_slashings) AS n_prop_slashings,
            list_length(attester_slashings) AS n_att_slashings
     FROM '{url}'
     WHERE list_length(proposer_slashings) > 0 
        OR list_length(attester_slashings) > 0
   """).fetchall()
   ```
3. Iterar por día durante Mayo 2022, acumular pérdidas por epoch
4. Cruzar con `canonical_beacon_validators` para calcular CL rewards (delta de balance activo)
5. Cruzar con `canonical_execution_block` para EIP-1559 burn
6. Computar GZS por epoch
7. Graficar GZS vs. eventos conocidos (stETH depeg)

---

## Tiempo estimado

| Tarea | Tiempo |
|-------|--------|
| Setup + query de prueba | 1 hora |
| Reconstrucción GZS Mayo 2022 (30 días × epochs) | 4-6 horas |
| Comparación con eventos conocidos + gráficos | 2-3 horas |
| **Total** | **~1 día de trabajo** |

---

## Implicaciones

Con este backtest hecho, el **Paper 3 del [[program_research|programa de investigación]]** deja de estar bloqueado. Y el **argumento empírico del [[program_economic|programa económico]]** (Hipótesis 2: Sharpe ratio superior en eventos de estrés) pasa de especulativo a demostrable.

---

## Fuente

Investigación realizada el 2026-04-24.

Referencias principales:
- `ethpandaops.io/data/xatu/`
- `github.com/ethpandaops/xatu-data`
- Nature Scientific Data 2025 (doi:10.7910/DVN/HG36LO) — cubre post-Merge solamente
- `arxiv.org/abs/2404.00644` — SoK: Liquid Staking Tokens
