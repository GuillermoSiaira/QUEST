# QUEST Demo Agent — ERC-8004 Spec para Codex

> Instrucción para Codex: Implementa exactamente lo que dice este spec.
> Es un contrato demo — no agregues lógica DeFi real, no agregues oracles externos,
> no agregues upgradability. El objetivo es demostrar el ciclo completo de la
> economía de agentes de QUEST en Sepolia.

---

## Contexto

QUESTCore (ya deployado en Sepolia `0xE81C6B16ecbEC8E4Aadc963e82B27c10c4ab10e7`)
publica métricas de riesgo on-chain cada epoch. Un agente ERC-8004 es un contrato
que:
1. Se registra en QUESTCore
2. Recibe señales de riesgo (llamada externa a `onQUESTSignal`)
3. Reacciona según su `riskTolerance`
4. Acumula reputación basada en si respetó la solvencia sistémica

---

## Archivo a crear

`contracts/QUESTDemoAgent.sol`

---

## Spec completo

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "./interfaces/IERC8004QuestAware.sol";

/**
 * @title QUESTDemoAgent
 * @notice Demo agent that implements IERC8004QuestAware.
 *         Demonstrates the QUEST agent economy: register → receive signals
 *         → react defensively → accumulate reputation.
 *
 * @dev This is a demonstration contract. In production, the onQUESTSignal
 *      callback would trigger real DeFi operations (pause lending, reduce
 *      leverage, halt withdrawals). Here it emits events and tracks state.
 */
contract QUESTDemoAgent is IERC8004QuestAware {

    // ── State ────────────────────────────────────────────────────────────────

    address public immutable owner;
    address public immutable questCore;

    /// @notice Max greyZoneScore this agent tolerates before going defensive (1e18 scale)
    /// Default: 0.3e18 (30% — conservative agent)
    uint256 private _riskTolerance;

    /// @notice Current operational mode
    bool public isDefensive;

    /// @notice Last epoch signal received
    uint256 public lastSignalEpoch;

    /// @notice Last greyZoneScore received
    uint256 public lastGreyZoneScore;

    /// @notice Count of times agent went defensive
    uint256 public defensiveCount;

    /// @notice Count of QUEST signals received total
    uint256 public signalCount;

    // ── Events ───────────────────────────────────────────────────────────────

    /// @notice Emitted every time a QUEST signal is received
    event QUESTSignalReceived(
        uint256 indexed epoch,
        uint256 greyZoneScore,
        uint256 thetaRisk,
        bool    isGreyZone,
        bool    wentDefensive
    );

    /// @notice Emitted when agent switches to defensive mode
    event DefensiveModeActivated(
        uint256 indexed epoch,
        uint256 greyZoneScore,
        string  reason
    );

    /// @notice Emitted when agent returns to normal mode
    event NormalModeRestored(
        uint256 indexed epoch,
        uint256 greyZoneScore
    );

    // ── Constructor ──────────────────────────────────────────────────────────

    constructor(address _questCore, uint256 riskTolerance_) {
        require(_questCore != address(0), "QUESTDemoAgent: zero questCore");
        require(riskTolerance_ <= 1e18, "QUESTDemoAgent: tolerance > 1e18");
        owner      = msg.sender;
        questCore  = _questCore;
        _riskTolerance = riskTolerance_ == 0 ? 3e17 : riskTolerance_; // default 0.3e18
    }

    // ── IERC8004QuestAware ───────────────────────────────────────────────────

    /**
     * @notice Called by QUEST operator when a new epoch signal is published.
     * @dev Anyone can call this — the agent decides internally how to react.
     *      In production: would pause positions, reduce leverage, etc.
     *      Here: emits events and flips isDefensive flag.
     */
    function onQUESTSignal(
        uint256 epoch,
        uint256 greyZoneScore,
        uint256 thetaRisk,
        uint256 thetaFinality,
        bool    isGreyZone_
    ) external override {
        lastSignalEpoch    = epoch;
        lastGreyZoneScore  = greyZoneScore;
        signalCount++;

        bool shouldBeDefensive = greyZoneScore >= _riskTolerance || isGreyZone_;
        bool wentDefensive     = false;

        if (shouldBeDefensive && !isDefensive) {
            isDefensive = true;
            defensiveCount++;
            wentDefensive = true;
            emit DefensiveModeActivated(
                epoch,
                greyZoneScore,
                isGreyZone_
                    ? "Grey Zone detected: hidden slashings masked by rewards"
                    : "greyZoneScore exceeded risk tolerance"
            );
        } else if (!shouldBeDefensive && isDefensive) {
            isDefensive = false;
            emit NormalModeRestored(epoch, greyZoneScore);
        }

        emit QUESTSignalReceived(epoch, greyZoneScore, thetaRisk, isGreyZone_, wentDefensive);
        emit StrategyAdjusted(epoch, greyZoneScore, bytes32(uint256(thetaRisk)));
    }

    function getRiskTolerance() external view override returns (uint256) {
        return _riskTolerance;
    }

    function getQUESTReputation() external view override returns (uint256) {
        // Reads reputation from QUESTCore storage
        // Interface: agentReputation(address) returns (uint256)
        (bool ok, bytes memory data) = questCore.staticcall(
            abi.encodeWithSignature("agentReputation(address)", address(this))
        );
        if (!ok || data.length == 0) return 0;
        return abi.decode(data, (uint256));
    }

    // ── Owner functions ──────────────────────────────────────────────────────

    /**
     * @notice Register this agent with QUESTCore.
     * @dev Calls QUESTCore.registerAgent(). Only owner.
     */
    function register() external {
        require(msg.sender == owner, "QUESTDemoAgent: not owner");
        (bool ok,) = questCore.call(abi.encodeWithSignature("registerAgent()"));
        require(ok, "QUESTDemoAgent: registration failed");
    }

    /**
     * @notice Update risk tolerance. Only owner.
     * @param newTolerance New tolerance in 1e18 scale (e.g., 5e17 = 0.5)
     */
    function setRiskTolerance(uint256 newTolerance) external {
        require(msg.sender == owner, "QUESTDemoAgent: not owner");
        require(newTolerance <= 1e18, "QUESTDemoAgent: tolerance > 1e18");
        _riskTolerance = newTolerance;
    }

    // ── View ─────────────────────────────────────────────────────────────────

    /**
     * @notice Returns a summary of the agent's current state.
     */
    function status() external view returns (
        bool    defensive,
        uint256 reputation,
        uint256 tolerance,
        uint256 signals,
        uint256 defensiveTriggers,
        uint256 lastEpoch
    ) {
        (bool ok, bytes memory data) = questCore.staticcall(
            abi.encodeWithSignature("agentReputation(address)", address(this))
        );
        uint256 rep = (ok && data.length > 0) ? abi.decode(data, (uint256)) : 0;

        return (
            isDefensive,
            rep,
            _riskTolerance,
            signalCount,
            defensiveCount,
            lastSignalEpoch
        );
    }
}
```

---

## Test a crear: `test/QUESTDemoAgent.t.sol`

Setup: deploy QUESTCore(address(this)) + QUESTDemoAgent(questCore, 3e17).

Tests requeridos (8):

1. `test_register_callsQuestCore`
   - Llama `agent.register()` desde owner
   - Assert `questCore.registeredAgents(address(agent)) == true`

2. `test_onQUESTSignal_healthyNoDefensive`
   - Call `onQUESTSignal(1, 1e17, 1000, 500, false)` (score 0.1 < tolerance 0.3)
   - Assert `agent.isDefensive() == false`
   - Assert `agent.signalCount() == 1`

3. `test_onQUESTSignal_exceedsTolerance_goesDefensive`
   - Call con `greyZoneScore = 5e17` (0.5 > tolerance 0.3)
   - Assert `agent.isDefensive() == true`
   - Assert `agent.defensiveCount() == 1`

4. `test_onQUESTSignal_greyZoneFlag_goesDefensive`
   - Call con `greyZoneScore = 1e17` pero `isGreyZone = true`
   - Assert `agent.isDefensive() == true`

5. `test_onQUESTSignal_recovers_toNormal`
   - Primero llamar con score alto (defensive=true)
   - Luego llamar con score bajo y isGreyZone=false
   - Assert `agent.isDefensive() == false`

6. `test_onQUESTSignal_emitsDefensiveModeActivated`
   - `vm.expectEmit` del evento `DefensiveModeActivated`

7. `test_setRiskTolerance_onlyOwner`
   - `vm.prank(address(0xBEEF))` → expect revert
   - Owner puede cambiar tolerance

8. `test_status_returnsCorrectFields`
   - Assert todos los campos de `status()` después de una señal

---

## Deploy script: agregar a `script/Deploy.s.sol`

Agregar al final del `run()` existente (después del deploy de QUESTCore):

```solidity
// Deploy demo agent apuntando al QUESTCore ya deployado
address questCoreAddr = vm.envAddress("QUEST_CORE_ADDRESS");
uint256 riskTolerance = 3e17; // 0.3 — conservative
QUESTDemoAgent agent = new QUESTDemoAgent(questCoreAddr, riskTolerance);
console2.log("QUESTDemoAgent deployed at:", address(agent));
```

Agregar el import al inicio del script:
```solidity
import "../contracts/QUESTDemoAgent.sol";
```

---

## Notas para Codex

- `onQUESTSignal` puede ser llamado por cualquiera (permissionless) — es correcto así
- `getQUESTReputation` usa staticcall para no depender del ABI de QUESTCore
- `register()` usa call low-level por la misma razón
- No agregues ReentrancyGuard — no hay ETH en este contrato
- El `StrategyAdjusted` event es del interface IERC8004QuestAware — ya está definido ahí
