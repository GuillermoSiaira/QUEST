# QUEST Fase 3 — AVS Node (Go) — Spec para Codex

> Instrucción para Codex: Implementa exactamente lo que dice este spec.
> No agregues EigenLayer BLS, no agregues multi-operador, no agregues aggregation.
> Esta es la versión v1: un único operador de confianza que publica on-chain.
> Si algo no está especificado, dejá un TODO comment y seguí.

---

## Contexto

QUEST es un oráculo macroprudencial para Ethereum. El risk-engine (Python, Cloud Run)
ya computa el Grey Zone Score cada epoch. El AVS node (este repo) es el puente que:

1. Lee el último epoch procesado desde `quest-api` (REST)
2. Convierte los datos al formato del contrato Solidity
3. Firma y publica on-chain en Sepolia vía `QUESTCore.reportEpochMetrics()`
4. Publica la señal θ vía `QUESTCore.publishGreyZoneScore()`

**No hay lógica de riesgo en Go.** Todo el cómputo ya ocurrió en Python.

---

## Arquitectura

```
quest-avs-node (Go binary — Cloud Run)
  Ticker cada POLL_INTERVAL_SECONDS
    → GET {QUEST_API_URL}/api/latest        (REST, JSON)
    → si epoch == lastSubmitted → skip
    → convertir EpochStatus → parámetros Solidity
    → computar dataHash
    → derivar señal θ desde greyZoneScore
    → tx: QUESTCore.reportEpochMetrics(...)
    → tx: QUESTCore.publishGreyZoneScore(...)
    → lastSubmitted = epoch
```

---

## Estructura de archivos a crear

```
quest-avs-node/
  go.mod
  main.go
  config/
    config.go
  oracle/
    runner.go        — loop principal
    api_client.go    — GET /api/latest desde quest-api
    chain_writer.go  — transacciones Ethereum (go-ethereum)
    theta.go         — derivación de señal θ
  Dockerfile
```

---

## 1. `quest-avs-node/go.mod`

```
module github.com/quest-protocol/quest-avs-node

go 1.22

require (
    github.com/ethereum/go-ethereum v1.14.8
    github.com/joho/godotenv v1.5.1
)
```

---

## 2. Variables de entorno (todas requeridas salvo DEFAULT_*)

```
QUEST_API_URL=https://quest-api-299259685359.us-central1.run.app
SEPOLIA_RPC_URL=https://eth-sepolia.g.alchemy.com/v2/<key>
OPERATOR_PRIVATE_KEY=<hex sin 0x>
QUEST_CORE_ADDRESS=0xE81C6B16ecbEC8E4Aadc963e82B27c10c4ab10e7
POLL_INTERVAL_SECONDS=384
LOG_LEVEL=INFO
```

---

## 3. `config/config.go`

```go
package config

import (
    "log"
    "os"
    "strconv"
    "github.com/joho/godotenv"
)

type Config struct {
    QuestAPIURL         string
    SepoliaRPCURL       string
    OperatorPrivateKey  string
    QuestCoreAddress    string
    PollIntervalSeconds int
}

func Load() *Config {
    _ = godotenv.Load() // ignora si no hay .env (Cloud Run usa env vars directas)

    pollInterval, err := strconv.Atoi(getEnv("POLL_INTERVAL_SECONDS", "384"))
    if err != nil {
        log.Fatal("POLL_INTERVAL_SECONDS must be an integer")
    }

    return &Config{
        QuestAPIURL:         requireEnv("QUEST_API_URL"),
        SepoliaRPCURL:       requireEnv("SEPOLIA_RPC_URL"),
        OperatorPrivateKey:  requireEnv("OPERATOR_PRIVATE_KEY"),
        QuestCoreAddress:    requireEnv("QUEST_CORE_ADDRESS"),
        PollIntervalSeconds: pollInterval,
    }
}

func requireEnv(key string) string {
    v := os.Getenv(key)
    if v == "" {
        log.Fatalf("required env var %s is not set", key)
    }
    return v
}

func getEnv(key, fallback string) string {
    if v := os.Getenv(key); v != "" {
        return v
    }
    return fallback
}
```

---

## 4. `oracle/api_client.go`

Hace GET a `{QUEST_API_URL}/api/latest` y deserializa el JSON.

### Struct EpochStatus (mapea el JSON de quest-api):

```go
package oracle

type RiskAssessment struct {
    Epoch                int64   `json:"epoch"`
    GrossSlashingLossEth float64 `json:"gross_slashing_loss_eth"`
    ClRewardsEth         float64 `json:"cl_rewards_eth"`
    BurnedEth            float64 `json:"burned_eth"`
    GreyZoneScore        float64 `json:"grey_zone_score"`
    RiskLevel            string  `json:"risk_level"` // "HEALTHY" | "GREY_ZONE" | "CRITICAL"
    HasRewardsData       bool    `json:"has_rewards_data"`
}

type EpochStatus struct {
    Epoch                 int64          `json:"epoch"`
    TotalValidators       int64          `json:"total_validators"`
    TotalActiveBalanceEth float64        `json:"total_active_balance_eth"`
    SlashedValidators     int64          `json:"slashed_validators"`
    SlashingPenaltyEth    float64        `json:"slashing_penalty_eth"`
    EpochRewardsEth       *float64       `json:"epoch_rewards_eth"`
    ParticipationRate     float64        `json:"participation_rate"`
    AvgGasPriceGwei       float64        `json:"avg_gas_price_gwei"`
    BurnedEth             float64        `json:"burned_eth"`
    LidoTvlEth            float64        `json:"lido_tvl_eth"`
    NetRebaseEth          *float64       `json:"net_rebase_eth"`
    IsGreyZone            bool           `json:"is_grey_zone"`
    Risk                  RiskAssessment `json:"risk"`
}
```

### Función:

```go
func FetchLatestEpoch(apiURL string) (*EpochStatus, error)
```

- GET `{apiURL}/api/latest`
- Timeout: 15 segundos
- Si status != 200: retornar error con el código HTTP
- Si body vacío o status 204: retornar `nil, nil` (sin datos todavía)

---

## 5. `oracle/theta.go`

Deriva la señal θ desde el Grey Zone Score. Reglas:

```go
package oracle

import "math/big"

type ThetaSignal struct {
    ThetaRisk       *big.Int // 0-10000
    ThetaGas        *big.Int // 0-10000
    ThetaLatency    *big.Int // 0-10000 (constante 5000 en v1)
    ThetaFinality   *big.Int // 0-10000
    ThetaIncentives *big.Int // 0-10000
}

func DeriveTheta(greyZoneScore float64) ThetaSignal
```

Lógica de `DeriveTheta`:

```
thetaRisk = min(10000, uint64(greyZoneScore * 10000))
  // si score=0.0 → 0, si score=1.0 → 10000, si score>1.0 → 10000

thetaGas      = 5000                        // constante v1
thetaLatency  = 5000                        // constante v1
thetaFinality = thetaRisk                   // igual al riesgo
thetaIncentives = 10000 - thetaRisk         // inverso
```

---

## 6. `oracle/chain_writer.go`

Usa `go-ethereum` para interactuar con QUESTCore en Sepolia.

### ABI de QUESTCore (solo las 2 funciones necesarias):

```json
[
  {
    "name": "reportEpochMetrics",
    "type": "function",
    "inputs": [
      {"name": "epoch",                "type": "uint64"},
      {"name": "greyZoneScore",        "type": "uint256"},
      {"name": "grossSlashingLossGwei","type": "uint256"},
      {"name": "clRewardsGwei",        "type": "uint256"},
      {"name": "burnedEthGwei",        "type": "uint256"},
      {"name": "participationRate",    "type": "uint32"},
      {"name": "riskLevel",            "type": "uint8"},
      {"name": "hasRewardsData",       "type": "bool"},
      {"name": "dataHash",             "type": "bytes32"}
    ],
    "outputs": []
  },
  {
    "name": "publishGreyZoneScore",
    "type": "function",
    "inputs": [
      {"name": "epoch",           "type": "uint64"},
      {"name": "thetaRisk",       "type": "uint256"},
      {"name": "thetaGas",        "type": "uint256"},
      {"name": "thetaLatency",    "type": "uint256"},
      {"name": "thetaFinality",   "type": "uint256"},
      {"name": "thetaIncentives", "type": "uint256"}
    ],
    "outputs": []
  }
]
```

### Conversiones Python float → Solidity uint:

```
greyZoneScore (uint256, 1e18):
    big.NewInt(int64(status.Risk.GreyZoneScore * 1e18))
    // CUIDADO: si score > 1.0, capear en 1e18 * 10 (10x max)

grossSlashingLossGwei (uint256):
    big.NewInt(int64(status.Risk.GrossSlashingLossEth * 1e9))

clRewardsGwei (uint256):
    big.NewInt(int64(status.Risk.ClRewardsEth * 1e9))

burnedEthGwei (uint256):
    big.NewInt(int64(status.Risk.BurnedEth * 1e9))

participationRate (uint32, 1e4):
    uint32(status.ParticipationRate * 10000)

riskLevel (uint8):
    map: "HEALTHY"→1, "GREY_ZONE"→2, "CRITICAL"→3, default→0
```

### dataHash:

```go
// keccak256(epoch_bytes || greyZoneScore_bytes)
// Usar crypto.Keccak256 de go-ethereum
// Concatenar: uint64 big-endian (8 bytes) + uint256 big-endian (32 bytes)
func computeDataHash(epoch uint64, greyZoneScore *big.Int) [32]byte
```

### Struct y constructor:

```go
type ChainWriter struct {
    client       *ethclient.Client
    auth         *bind.TransactOpts
    contractAddr common.Address
    abi          abi.ABI
}

func NewChainWriter(rpcURL, privateKeyHex, contractAddr string) (*ChainWriter, error)
```

### Métodos:

```go
func (w *ChainWriter) ReportEpochMetrics(status *EpochStatus) (*types.Transaction, error)
func (w *ChainWriter) PublishGreyZoneScore(epoch uint64, theta ThetaSignal) (*types.Transaction, error)
```

Ambos métodos deben:
- Estimar gas antes de enviar (`EstimateGas`)
- Multiplicar gas estimate por 1.2 (margen de seguridad)
- Loguear: `epoch, txHash, gasUsed`
- Retornar error si la tx revierte

---

## 7. `oracle/runner.go`

Loop principal:

```go
package oracle

type Runner struct {
    cfg         *config.Config
    chainWriter *ChainWriter
    lastEpoch   int64
}

func NewRunner(cfg *config.Config) (*Runner, error)

func (r *Runner) Run(ctx context.Context)
// Loop: ticker cada cfg.PollIntervalSeconds
// En cada tick:
//   1. FetchLatestEpoch(cfg.QuestAPIURL)
//   2. Si nil o epoch <= r.lastEpoch → skip, loguear "no new epoch"
//   3. ReportEpochMetrics(status)
//   4. Si error → loguear y continuar (no parar el loop)
//   5. DeriveTheta(status.Risk.GreyZoneScore)
//   6. PublishGreyZoneScore(epoch, theta)
//   7. r.lastEpoch = epoch
//   8. Loguear: "Epoch {N} submitted | score={X} | risk={Y} | txs={hash1},{hash2}"
```

---

## 8. `main.go`

```go
package main

import (
    "context"
    "log"
    "os/signal"
    "syscall"

    "github.com/quest-protocol/quest-avs-node/config"
    "github.com/quest-protocol/quest-avs-node/oracle"
)

func main() {
    cfg := config.Load()

    runner, err := oracle.NewRunner(cfg)
    if err != nil {
        log.Fatalf("failed to initialize runner: %v", err)
    }

    ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGTERM, syscall.SIGINT)
    defer stop()

    log.Printf("QUEST AVS Node started")
    log.Printf("  Contract: %s", cfg.QuestCoreAddress)
    log.Printf("  API:      %s", cfg.QuestAPIURL)
    log.Printf("  Interval: %ds", cfg.PollIntervalSeconds)

    runner.Run(ctx)
    log.Println("QUEST AVS Node stopped.")
}
```

---

## 9. `Dockerfile`

```dockerfile
FROM golang:1.22-alpine AS builder
WORKDIR /build
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN go build -o quest-avs-node .

FROM alpine:3.19
RUN apk add --no-cache ca-certificates
WORKDIR /app
COPY --from=builder /build/quest-avs-node .
ENV PORT=8080
EXPOSE 8080
CMD ["./quest-avs-node"]
```

---

## 10. Notas para Codex

- `go.sum` se genera con `go mod tidy` — no lo escribas a mano
- El `RiskLevel` enum en Solidity es `uint8`: UNSPECIFIED=0, HEALTHY=1, GREY_ZONE=2, CRITICAL=3
- El `bind.TransactOpts` debe configurar `GasLimit` manualmente (no usar `0` que activa estimación automática de ethclient que puede fallar)
- Para la chain ID de Sepolia usar `big.NewInt(11155111)`
- No implementar HTTP server — este binario no expone endpoints, solo consume y escribe
- El loop debe ser cancelable vía context (para graceful shutdown en Cloud Run)

---

## Deployment (después de que Codex entregue)

```bash
# Build y push a GCR
gcloud builds submit --config=cloudbuild-avs.yaml --project=quest-493015 .

# Deploy en Cloud Run
gcloud run deploy quest-avs-node \
  --image=gcr.io/quest-493015/quest-avs-node:latest \
  --region=us-central1 \
  --project=quest-493015 \
  --min-instances=1 \
  --set-env-vars="QUEST_API_URL=...,QUEST_CORE_ADDRESS=0xE81C6B16ecbEC8E4Aadc963e82B27c10c4ab10e7" \
  --set-secrets="OPERATOR_PRIVATE_KEY=operator-private-key:latest,SEPOLIA_RPC_URL=sepolia-rpc-url:latest" \
  --no-allow-unauthenticated
```

**OPERATOR_PRIVATE_KEY y SEPOLIA_RPC_URL deben ir en Secret Manager, nunca como env vars directas.**
