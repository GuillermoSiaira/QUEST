# QUEST Contracts — Spec para Fase 2 (Sepolia)

> Instrucción para Codex: Implementa exactamente lo que dice este spec. No agregues
> upgradeability, proxies, ni dependencias de OpenZeppelin. No inventes funciones extra.
> Si algo no está especificado, déjalo sin implementar y agrega un TODO comment.

---

## Contexto

QUEST es un oráculo macroprudencial para Ethereum. Computa el Grey Zone Score off-chain
(Python, GCP Cloud Run) y lo publica on-chain. El contrato NO ejecuta lógica de riesgo —
solo almacena y emite señales. Permissionless por diseño: cualquiera puede leer, solo el
operador puede escribir.

El off-chain calcula:
- `greyZoneScore = grossSlashingLoss / (clRewards + burnedEth)` (scaled 1e18)
- Thresholds: HEALTHY < 0.5e18, GREY_ZONE [0.5e18, 1e18), CRITICAL >= 1e18

---

## Archivos a crear / modificar

| Archivo | Acción |
|---|---|
| `contracts/interfaces/IERC8033.sol` | Modificar: renombrar QSR → GreyZoneScore |
| `contracts/interfaces/IERC8004QuestAware.sol` | Modificar: actualizar firmas para usar `greyZoneScore` |
| `contracts/QUESTCore.sol` | Modificar: refactor completo según spec |
| `test/QUESTCore.t.sol` | Crear: tests Foundry |
| `script/Deploy.s.sol` | Crear: deploy script para Sepolia |
| `foundry.toml` | Crear: config Foundry |

---

## 1. `contracts/interfaces/IERC8033.sol`

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface IERC8033 {
    /// @notice Grey Zone Score scaled 1e18. HEALTHY < 0.5e18, GREY_ZONE < 1e18, CRITICAL >= 1e18.
    function getLatestGreyZoneScore() external view returns (uint256);

    /// @notice PMC signal vector (θ). All values scaled 0-10000.
    function getLatestPMC() external view returns (
        uint256 thetaRisk,
        uint256 thetaGas,
        uint256 thetaFinality
    );

    /// @notice True if latest epoch has hidden slashings masked by positive rewards.
    function isGreyZone() external view returns (bool);

    /// @notice Epoch temporal density D_k. Implementation-defined scaling.
    function getEpochDensity() external view returns (uint256);
}
```

---

## 2. `contracts/interfaces/IERC8004QuestAware.sol`

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface IERC8004QuestAware {
    event StrategyAdjusted(
        uint256 indexed epoch,
        uint256 greyZoneScore,
        bytes32 actionTaken
    );

    /// @notice Called when QUEST publishes a new PMC signal.
    /// @param epoch          Current epoch number
    /// @param greyZoneScore  Risk score scaled 1e18
    /// @param thetaRisk      Risk coefficient 0-10000
    /// @param thetaFinality  Finality risk 0-10000
    /// @param isGreyZone     True if hidden slashings detected
    function onQUESTSignal(
        uint256 epoch,
        uint256 greyZoneScore,
        uint256 thetaRisk,
        uint256 thetaFinality,
        bool isGreyZone
    ) external;

    /// @notice Agent's declared max acceptable greyZoneScore (scaled 1e18).
    function getRiskTolerance() external view returns (uint256);

    /// @notice Agent's QUEST reputation score (0-10000).
    function getQUESTReputation() external view returns (uint256);
}
```

---

## 3. `contracts/QUESTCore.sol`

### Enums

```solidity
enum RiskLevel {
    UNSPECIFIED, // 0 — dato no disponible
    HEALTHY,     // 1 — greyZoneScore < 0.5e18
    GREY_ZONE,   // 2 — 0.5e18 <= greyZoneScore < 1e18
    CRITICAL     // 3 — greyZoneScore >= 1e18
}
```

Estos valores deben coincidir con el enum `RiskLevel` en `risk-engine/quest.proto`.

### Structs

```solidity
struct EpochMetrics {
    uint64  epoch;
    uint256 greyZoneScore;          // scaled 1e18
    uint256 grossSlashingLossGwei;
    uint256 clRewardsGwei;
    uint256 burnedEthGwei;
    uint32  participationRate;      // scaled 1e4 (10000 = 100%)
    RiskLevel riskLevel;
    bool    hasRewardsData;         // false si no hay datos de rewards del epoch
    bytes32 dataHash;               // keccak256(abi.encode(todos los campos)) — para verificación AVS futura
    uint64  reportedAt;             // block.timestamp en el momento del reporte
}

struct PMCSignal {
    uint64  epoch;
    uint256 thetaRisk;              // 0-10000
    uint256 thetaGas;               // 0-10000
    uint256 thetaLatency;           // 0-10000
    uint256 thetaFinality;          // 0-10000
    uint256 thetaIncentives;        // 0-10000
    uint64  publishedAt;            // block.timestamp
}
```

### State variables

```solidity
address public immutable operator;
EpochMetrics public latestMetrics;
PMCSignal    public latestPMC;
mapping(address => uint256) public agentReputation;  // 0-10000
mapping(address => bool)    public registeredAgents;
```

### Events

```solidity
event EpochMetricsReported(
    uint64  indexed epoch,
    uint256 greyZoneScore,
    RiskLevel riskLevel,
    bool    hasRewardsData,
    uint64  reportedAt
);

event GreyZoneScorePublished(
    uint64  indexed epoch,
    uint256 thetaRisk,
    uint256 thetaFinality,
    uint64  publishedAt
);

event AgentReputationUpdated(
    address indexed agent,
    uint256 oldScore,
    uint256 newScore
);

event AgentRegistered(address indexed agent);
```

### Constructor

```solidity
constructor(address _operator) {
    require(_operator != address(0), "QUESTCore: zero operator");
    operator = _operator;
}
```

### Modifier

```solidity
modifier onlyOperator() {
    require(msg.sender == operator, "QUESTCore: not operator");
    _;
}
```

### Write functions (onlyOperator)

#### `reportEpochMetrics`
```solidity
function reportEpochMetrics(
    uint64  epoch,
    uint256 greyZoneScore,
    uint256 grossSlashingLossGwei,
    uint256 clRewardsGwei,
    uint256 burnedEthGwei,
    uint32  participationRate,
    RiskLevel riskLevel,
    bool    hasRewardsData,
    bytes32 dataHash
) external onlyOperator
```
Almacena en `latestMetrics`. `reportedAt = uint64(block.timestamp)`.
Emite `EpochMetricsReported`.

#### `publishGreyZoneScore`
```solidity
function publishGreyZoneScore(
    uint64  epoch,
    uint256 thetaRisk,
    uint256 thetaGas,
    uint256 thetaLatency,
    uint256 thetaFinality,
    uint256 thetaIncentives
) external onlyOperator
```
Almacena en `latestPMC`. `publishedAt = uint64(block.timestamp)`.
Emite `GreyZoneScorePublished`.

#### `updateAgentReputation`
```solidity
function updateAgentReputation(
    address agent,
    uint256 newScore
) external onlyOperator
```
`newScore` debe ser <= 10000. Revert con `"QUESTCore: score > 10000"` si no.
Emite `AgentReputationUpdated(agent, oldScore, newScore)`.

### Public functions

#### `registerAgent`
```solidity
function registerAgent() external
```
Sets `registeredAgents[msg.sender] = true`. Emite `AgentRegistered`.
No revert si ya registrado — idempotente.

### IERC8033 view functions

```solidity
function getLatestGreyZoneScore() external view returns (uint256) {
    return latestMetrics.greyZoneScore;
}

function getLatestPMC() external view returns (
    uint256 thetaRisk,
    uint256 thetaGas,
    uint256 thetaFinality
) {
    return (latestPMC.thetaRisk, latestPMC.thetaGas, latestPMC.thetaFinality);
}

function isGreyZone() external view returns (bool) {
    return latestMetrics.riskLevel == RiskLevel.GREY_ZONE
        || latestMetrics.riskLevel == RiskLevel.CRITICAL;
}

function getEpochDensity() external view returns (uint256) {
    // D_k simplificado: participación × inverso del score normalizado
    // Si no hay datos de rewards, retornar solo participación
    if (!latestMetrics.hasRewardsData) {
        return latestMetrics.participationRate;
    }
    uint256 riskFactor = latestMetrics.greyZoneScore > 1e18
        ? 1e18
        : latestMetrics.greyZoneScore;
    // D_k: participación ponderada por riesgo inverso
    return (uint256(latestMetrics.participationRate) * (1e18 - riskFactor)) / 1e18;
}
```

---

## 4. `test/QUESTCore.t.sol`

Usar Foundry (`forge-std/Test.sol`). Crear contrato `QUESTCoreTest is Test`.

Setup: deploy `QUESTCore(address(this))` — el test contract es el operador.

### Tests requeridos:

1. `test_reportEpochMetrics_storesCorrectly`
   - Llama `reportEpochMetrics` con valores conocidos
   - Assert `latestMetrics.epoch`, `latestMetrics.greyZoneScore`, `latestMetrics.riskLevel`

2. `test_reportEpochMetrics_revertsIfNotOperator`
   - `vm.prank(address(0xBEEF))`
   - Expect revert `"QUESTCore: not operator"`

3. `test_publishGreyZoneScore_emitsEvent`
   - `vm.expectEmit(true, false, false, true)`
   - Verify `GreyZoneScorePublished` event fields

4. `test_isGreyZone_trueWhenGreyZone`
   - Report with `RiskLevel.GREY_ZONE`
   - Assert `isGreyZone() == true`

5. `test_isGreyZone_trueWhenCritical`
   - Report with `RiskLevel.CRITICAL`
   - Assert `isGreyZone() == true`

6. `test_isGreyZone_falseWhenHealthy`
   - Report with `RiskLevel.HEALTHY`
   - Assert `isGreyZone() == false`

7. `test_updateAgentReputation_setsScore`
   - Call `updateAgentReputation(alice, 5000)`
   - Assert `agentReputation[alice] == 5000`

8. `test_updateAgentReputation_revertsAbove10000`
   - Expect revert `"QUESTCore: score > 10000"`
   - Call `updateAgentReputation(alice, 10001)`

9. `test_registerAgent_idempotent`
   - Call `registerAgent()` twice
   - Assert `registeredAgents[address(this)] == true` (no revert)

10. `test_dataHash_storedCorrectly`
    - Pasar `bytes32(keccak256("test"))` como `dataHash`
    - Assert `latestMetrics.dataHash == keccak256("test")`

---

## 5. `script/Deploy.s.sol`

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Script.sol";
import "../contracts/QUESTCore.sol";

contract DeployQUEST is Script {
    function run() external {
        address operator = vm.envAddress("QUEST_OPERATOR_ADDRESS");
        vm.startBroadcast();
        QUESTCore core = new QUESTCore(operator);
        vm.stopBroadcast();
        console2.log("QUESTCore deployed at:", address(core));
        console2.log("Operator:", operator);
    }
}
```

---

## 6. `foundry.toml`

```toml
[profile.default]
src     = "contracts"
test    = "test"
script  = "script"
out     = "out"
libs    = ["lib"]
solc    = "0.8.24"

[rpc_endpoints]
holesky = "${HOLESKY_RPC_URL}"
mainnet = "${ALCHEMY_RPC_URL}"

[etherscan]
holesky = { key = "${ETHERSCAN_API_KEY}", url = "https://api-holesky.etherscan.io/api" }
```

---

## Variables de entorno requeridas para deploy

```
HOLESKY_RPC_URL=          # ej: https://ethereum-holesky.publicnode.com
QUEST_OPERATOR_ADDRESS=   # EOA o multisig que firmará los reportes
ETHERSCAN_API_KEY=         # para verificar el contrato
PRIVATE_KEY=               # del deployer (no tiene que ser el mismo que operator)
```

Comando de deploy:
```bash
forge script script/Deploy.s.sol:DeployQUEST \
  --rpc-url holesky \
  --broadcast \
  --verify \
  -vvvv
```
