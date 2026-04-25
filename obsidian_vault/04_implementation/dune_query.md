---
name: Dune Analytics — Query de estimación empírica de λ
description: Metodología y SQL para estimar λ̂ por wallet on-chain y testear colapso de F(λ,t) durante mayo 2022
type: implementation
estado: pendiente
actualizado: 2026-04-25
tags: [dune, empirico, lambda, datos, paper2]
---

# Dune Query — Estimación Empírica de λ

El bloque de trabajo que desbloquea el Paper 2 (empírico).

---

## Qué es Dune Analytics

[Dune](https://dune.com) indexa toda la blockchain de Ethereum en tablas SQL (SparkSQL/DuneSQL). Permite queries tipo "dame el balance de stETH de cada wallet semana a semana durante 2021-2023" sin correr un nodo propio.

Es gratuito hasta cierto volumen de queries. Los datos son públicos e inmutables.

---

## Qué necesitamos extraer

Para estimar λ̂ por wallet por período necesitamos tres observables:

| Variable | Qué es | Fuente en Dune |
|----------|--------|----------------|
| **α̂(i,t)** | stETH_value / portfolio_total por wallet | `tokens.erc20_balances` + `prices.usd` |
| **s(t)** | Proxy del signal = 1 − (precio stETH / precio ETH) | `dex.trades` o `prices.usd` |
| **σ²(s(t))** | Varianza rolling 4-semanas del signal | Derivada de s(t) |

Con esos tres datos, λ̂ se estima como:

```
λ̂(i,t) = (1 − α̂(i,t)) · 2·E(R) / σ²(s(t))
```

Donde E(R) = 0.0075 (rendimiento esperado por epoch, ≈ 4.5% APY / 225).

---

## La hipótesis a testear

**H1**: Var(F̂(λ,t)) colapsó durante mayo 2022 y se recuperó después.

Es decir: antes del depeg, los agentes tenían distribuciones de λ dispersas. Durante el depeg, todos los agentes exhibieron el mismo comportamiento (λ homogéneo implícito) → corrida. Después, la distribución se recuperó.

Esto valdría como evidencia empírica del mecanismo propuesto.

---

## Población objetivo

- **Top 500-1000 wallets** por tamaño de posición stETH
- **Período**: 2021-01-01 → 2023-12-31 (156 semanas)
- **Excluir**: contratos de protocolo (Lido, Curve, Aave pools) — solo EOAs o multisigs de usuarios

El stETH contract en Ethereum mainnet: `0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84`

---

## Query SQL (DuneSQL)

### Step 1: Top holders de stETH (snapshot semanal)

```sql
-- stETH weekly balance per wallet, top 1000 holders
WITH steth_transfers AS (
    SELECT
        date_trunc('week', block_time) AS week,
        "to"   AS wallet,
        value / 1e18 AS amount
    FROM erc20_ethereum.evt_Transfer
    WHERE contract_address = 0xae7ab96520de3a18e5e111b5eaab095312d7fe84
      AND block_time BETWEEN timestamp '2021-01-01' AND timestamp '2023-12-31'

    UNION ALL

    SELECT
        date_trunc('week', block_time) AS week,
        "from" AS wallet,
        -value / 1e18 AS amount
    FROM erc20_ethereum.evt_Transfer
    WHERE contract_address = 0xae7ab96520de3a18e5e111b5eaab095312d7fe84
      AND block_time BETWEEN timestamp '2021-01-01' AND timestamp '2023-12-31'
),

weekly_balances AS (
    SELECT
        week,
        wallet,
        SUM(SUM(amount)) OVER (
            PARTITION BY wallet
            ORDER BY week
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS steth_balance
    FROM steth_transfers
    WHERE wallet != 0x0000000000000000000000000000000000000000
    GROUP BY week, wallet
),

-- Filter to wallets that held meaningful stETH at some point
top_wallets AS (
    SELECT wallet
    FROM weekly_balances
    WHERE steth_balance > 1.0    -- at least 1 stETH at some point
    GROUP BY wallet
    ORDER BY MAX(steth_balance) DESC
    LIMIT 1000
)

SELECT
    wb.week,
    wb.wallet,
    wb.steth_balance
FROM weekly_balances wb
INNER JOIN top_wallets tw ON wb.wallet = tw.wallet
WHERE wb.steth_balance > 0
ORDER BY wb.week, wb.steth_balance DESC
```

### Step 2: Precio stETH/ETH semanal (proxy del signal s(t))

```sql
-- stETH/ETH price ratio from Curve pool trades
-- stETH-ETH pool: 0xDC24316b9AE028F1497c275EB9192a3Ea0f67022
WITH steth_prices AS (
    SELECT
        date_trunc('week', block_time) AS week,
        AVG(token_bought_amount / token_sold_amount) AS steth_eth_ratio
    FROM dex.trades
    WHERE blockchain = 'ethereum'
      AND (
        -- Curve stETH/ETH pool
        project_contract_address = 0xdc24316b9ae028f1497c275eb9192a3ea0f67022
        OR project_contract_address = 0x828b154032950c8ff7cf8085d841723db2696056
      )
      AND block_time BETWEEN timestamp '2021-01-01' AND timestamp '2023-12-31'
      AND token_bought_amount > 0
      AND token_sold_amount > 0
    GROUP BY 1
)

SELECT
    week,
    steth_eth_ratio,
    1 - steth_eth_ratio AS signal_s,  -- depeg proxy: 0 = perfect peg, +0.07 = -7% depeg
    AVG(1 - steth_eth_ratio) OVER (
        ORDER BY week
        ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
    ) AS signal_ma4w,
    STDDEV(1 - steth_eth_ratio) OVER (
        ORDER BY week
        ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
    ) AS signal_std4w
FROM steth_prices
ORDER BY week
```

### Step 3: Computar α̂ y λ̂ (Python post-Dune)

```python
# Después de exportar los resultados de Dune como CSV:

import pandas as pd
import numpy as np

E_R = 0.0075
SIGMA_BASE = 0.05
K = np.log(10)

balances = pd.read_csv("dune_balances.csv")   # week, wallet, steth_balance
prices   = pd.read_csv("dune_prices.csv")     # week, signal_s, signal_std4w

# Merge y computar α̂ por wallet
# Asumimos ETH portfolio ≈ stETH * ETH_price (simplificación inicial)
# Para más precisión: cruzar con ETH balance vía eth_ethereum.traces

df = balances.merge(prices, on="week")
df["sigma_sq"] = SIGMA_BASE**2 * np.exp(K * df["signal_s"].clip(lower=0))

# λ̂: asume α̂ ≈ fracción de posición relativa al máximo histórico del wallet
df["alpha_hat"] = df.groupby("wallet")["steth_balance"].transform(
    lambda x: x / x.rolling(52, min_periods=1).max()
).clip(0, 1)

df["lambda_hat"] = (
    (1 - df["alpha_hat"]) * 2 * E_R / df["sigma_sq"]
).clip(0, 10)  # cap outliers

# Distribución F̂(λ,t): varianza de λ̂ entre wallets por semana
f_lambda_var = (
    df.groupby("week")["lambda_hat"]
    .agg(["mean", "std", "count"])
    .rename(columns={"std": "var_f_lambda"})
)

print(f_lambda_var.loc["2022-04":"2022-07"])  # foco en mayo 2022
```

---

## Qué esperamos ver

```
Var(F̂(λ,t))

 0.8 │      ┌─┐
     │      │ │
 0.5 │──────┘ └──────────────
     │  pre-depeg    post
 0.1 │         ═══
     │      mayo 2022
     └──────────────────────→ semanas
```

- **Pre-depeg**: Var alto → distribución dispersa → heterogeneidad
- **Durante**: Var colapsa → todos exhiben el mismo λ alto (pánico)
- **Post-depeg**: Var se recupera → heterogeneidad restaurada

Si este patrón aparece en los datos, es evidencia directa de la tesis.

---

## Limitaciones conocidas

| Limitación | Impacto | Mitigación |
|------------|---------|------------|
| α̂ subestima portfolio real (solo stETH, ignora ETH en wallet) | λ̂ sesgado hacia arriba | Nota metodológica; no invalida el patrón de varianza |
| Contratos de protocolo en el top 1000 | Distorsiona F̂(λ) | Filtrar por tipo de cuenta (EOA check) |
| La aproximación de α depende del máximo histórico | Introduce ruido | Usar ventana rolling de 12 semanas como denominador |
| stETH/ETH ratio de Curve incluye slippage | s(t) ruidoso | MA4w suaviza |

---

## Esfuerzo estimado

| Tarea | Tiempo |
|-------|--------|
| Escribir y debuggear queries en Dune | 4-6 horas |
| Exportar CSVs y correr análisis Python | 2-3 horas |
| Gráficos de Var(F̂(λ,t)) vs eventos | 2-3 horas |
| **Total** | **~1-2 días** |

---

## Conexiones en vault

→ [[research_strategy]] — Paper 2 (empírico) depende de esto
→ [[historical_dataset]] — datos del consensus layer (complementarios)
→ [[utility_function]] — modelo de donde surge la fórmula de λ̂
