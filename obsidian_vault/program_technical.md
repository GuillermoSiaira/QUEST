---
tags: [program, technical, api, architecture]
tipo: programa
prioridad: 2
estado: esqueleto
fecha: 2026-04-24
---

# Programa Técnico — La API que hace el producto defendible

## Tesis

La infraestructura técnica de QUEST v2 debe soportar dos productos: **calibraciones curadas** y **prueba verificable de ejecución**. Todo lo demás es commodity. El stack actual (risk-engine + FastAPI + Sepolia) cubre el 30% de lo necesario.

---

## Arquitectura target (v2)

```
┌──────────────────────────────────────────────────────┐
│  CAPA 4 — Certificación de ejecución                 │
│  ZK proof o AVS attestation: "agente X reportó U_t   │
│  = valor_declarado en epoch e, con exposure α_t"     │
│  → ERC-8004 reputation badge                         │
└──────────────────────┬───────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────┐
│  CAPA 3 — Librería de calibraciones curadas          │
│  {conservative, moderate, aggressive, custom}         │
│  Validadas con backtest (Luna, 3AC, etc.)            │
│  Publicadas como NFT o registro on-chain              │
└──────────────────────┬───────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────┐
│  CAPA 2 — API de utilidad (esto es lo NUEVO)         │
│  GET /utility/compute?profile=X&gzs=Y                │
│  POST /utility/subscribe (WebSocket)                 │
│  GET /utility/backtest?profile=X&event=Y             │
└──────────────────────┬───────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────┐
│  CAPA 1 — GZS (lo que ya existe)                     │
│  risk-engine → Firestore → IPFS/Filecoin             │
└──────────────────────────────────────────────────────┘
```

Capa 1 existe. Capas 2-4 son construcción.

---

## Diseño de los endpoints — esqueleto inicial

### Endpoint público (free tier)

```
GET /api/v2/signal/current
  → { gzs: 0.34, epoch: 441023, risk_level: "HEALTHY", timestamp: ... }

GET /api/v2/signal/history?n=100
  → [ { epoch: N, gzs: ..., ... }, ... ]
```

### Endpoint premium (autenticado, requiere contrato)

```
GET /api/v2/utility/compute?profile=moderate&gzs=0.7&capital=1000000
  → {
      exposure_target: 520000,  // α × capital
      exposure_ratio: 0.52,
      utility_value: 0.0051,
      calibration: { lambda: 0.6, sigma_base: 0.05, k: 2.303 },
      calibration_version: "v1.2",
      confidence_interval: [0.48, 0.56],  // basado en backtest
      signature: "0x..."  // attestation del operator QUEST
    }

POST /api/v2/agent/register
  Body: { agent_address: "0x...", declared_profile: "moderate", ... }
  → { registration_id: "...", reputation_token_id: 42 }

POST /api/v2/agent/attest
  Body: { agent_address: "0x...", epoch: N, reported_exposure: α, signed_proof: "0x..." }
  → { attestation_hash: "0x...", published_onchain_tx: "0x..." }
```

### Endpoint de backtest (el que justifica pagar)

```
GET /api/v2/backtest/event/{event_id}?profile=X
  → {
      event: "LUNA_collapse_2022",
      dates: ["2022-05-09", "2022-05-15"],
      agent_without_quest: { drawdown: -0.42, sharpe: -1.8 },
      agent_with_quest_profile: { drawdown: -0.12, sharpe: 0.4,
                                    reduced_at_epoch: N, to_exposure: 0.15 }
    }
```

---

## Decisión crítica — ¿ZK o AVS para la certificación?

### Opción A — AVS en EigenLayer
- **Pro**: ya estamos en esa dirección (quest-avs-node existe)
- **Pro**: seguridad criptoeconómica validada
- **Contra**: requiere operadores BLS, multi-sig, complejidad alta
- **Timeline**: 6-9 meses

### Opción B — ZK proof de ejecución
- **Pro**: elegante, verificación matemática no económica
- **Pro**: trend correcto (ZK is the future)
- **Contra**: probar "ejecuté esta función" en ZK es caro/complejo para funciones con `exp()`
- **Timeline**: 12+ meses con herramientas actuales

### Opción C — Attestation firmada + challenge period (v1 simple)
- **Pro**: funciona en 2 semanas
- **Pro**: suficiente para adopción temprana
- **Contra**: confianza en operador QUEST
- **Timeline**: inmediato

Mi recomendación: **C ahora, migrar a A en 6 meses, B es investigación posterior**. Construir para C nos permite tener producto vivo mientras maduran las otras capas.

---

## Stack concreto sugerido

| Componente | Tech | Estado |
|-----------|------|--------|
| GZS engine | Python + aiohttp (existe) | ✅ |
| API pública | FastAPI + Cloud Run (existe) | ✅ |
| Base de datos calibraciones | Postgres (nuevo) | 🔴 |
| Backtest engine | Python + pandas + datos históricos Beacon | 🔴 |
| Attestation service | Go (extender quest-avs-node) | 🟡 |
| Registro on-chain | Extender QUESTCore.sol + nuevo QUESTRegistry.sol | 🟡 |
| Reputation ERC-8004 | Solidity nuevo | 🔴 |

---

## Gaps que bloquean este programa

1. ~~**Dataset histórico**: no tenemos datos de slashing + rewards pre-2026~~ **RESUELTO** — Xatu (EthPandaOps) publica datos desde genesis 2020 en parquet files gratis. Ver [[historical_dataset]].
2. **Calibraciones validadas**: primera validación con stETH depeg Mayo 2022 — factible en horas con Xatu.
3. **Definición del profile schema**: ¿qué parámetros son negociables vs. fijos? ¿se versionan?

---

## Próximas acciones concretas

- [ ] Escribir OpenAPI spec (YAML) de los endpoints v2 arriba — 1 día
- [ ] Prototipo de backtest engine sobre datos sintéticos — 2-3 días
- [ ] Diseño del schema de "calibration profile" — 1 día
- [ ] Investigar: ¿tenemos acceso a datos históricos Beacon suficientes para backtest? — 1 día research

→ Ver [[program_economic]] para quién paga esto
→ Ver [[program_research]] para qué publicamos sobre esto
