---
tags: [implementation, solidity, contracts]
tipo: referencia
estado: sepolia
---

# Contratos Solidity

Implementación on-chain del framework QUEST en Sepolia.

---

## Contratos desplegados

| Contrato | Red | Address |
|----------|-----|---------|
| `QUESTCore.sol` | Sepolia | `0xE81C6B16ecbEC8E4Aadc963e82B27c10c4ab10e7` |
| `QUESTAwareProtocol.sol` | Sepolia | `0xD693C783AbDCe3B53b2C33D8fEB0ff4E70f12735` |

**Operator**: `0xBb3272F387dE5A2c2e3906d24EfaC460a7013f2C`

---

## QUESTCore.sol — Estructura de datos on-chain

```solidity
struct EpochMetrics {
    uint64  epoch;
    uint256 greyZoneScore;          // scaled 1e18
    uint256 grossSlashingLossGwei;
    uint256 clRewardsGwei;
    uint256 burnedEthGwei;
    uint32  participationRate;      // scaled 1e4
    RiskLevel riskLevel;            // HEALTHY | GREY_ZONE | CRITICAL
    bytes32 dataHash;               // keccak256 para verificación AVS
    uint64  reportedAt;
}
```

---

## QUESTAgent.sol — Función de utilidad on-chain

Implementa el [[utility_function|framework de utilidad]] exactamente como está especificado, usando **PRBMath UD60x18** para aritmética de punto fijo:

```solidity
// σ²(GZS) = σ_base² · e^(k·GZS)
UD60x18 gzs = ud(greyZoneScore);  // ya está scaled 1e18
UD60x18 sigma2 = sigma_base_sq.mul(gzs.mul(k_param).exp());

// U = E(R) - (λ/2)·σ²
UD60x18 utility = expected_return.sub(lambda_param.mul(sigma2).div(TWO));

// α = max(0, U/E(R))
UD60x18 alpha = utility.lte(ZERO) ? ZERO : utility.div(expected_return);
```

La función de utilidad on-chain coincide exactamente con la especificación matemática.

---

## Interfaces ERC

| Interfaz | Descripción |
|----------|-------------|
| `IERC8033.sol` | Oracle macroprudencial — publica GZS y señal θ on-chain |
| `IERC8004QuestAware.sol` | Protocolo DeFi que consume señales QUEST |

*Nota: ERC-8033 y ERC-8004 son propuestas de QUEST, no estándares ratificados.*

---

## Tests

```
test/QUESTCore.t.sol          — 10 casos (Foundry)
test/QUESTAwareProtocol.t.sol — 8 casos (Foundry)
```

`forge test` — 18/18 verde.
