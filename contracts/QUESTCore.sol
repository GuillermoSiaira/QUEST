// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "./interfaces/IERC8033.sol";
import "./interfaces/IERC8004QuestAware.sol";

/**
 * @title QUESTCore
 * @notice Sovereign Stability Agent — Macroprudential Oracle for Ethereum
 * @dev Stores Computational Monetary Policy (θ) and Quantum Solvency Ratio (QSR)
 *      computed off-chain by the QUEST oracle node (Python/Qiskit).
 *      This contract is NON-COERCIVE — it only emits signals.
 *      Agents opt-in to react to θ in exchange for ERC-8004 reputation.
 */
contract QUESTCore is IERC8033 {

    // --- State ---

    address public immutable operator;

    /// @notice Latest epoch metrics reported by the oracle node
    EpochMetrics public latestMetrics;

    /// @notice Computational Monetary Policy signal vector
    PMCSignal public latestPMC;

    /// @notice Agent reputation scores (ERC-8004)
    mapping(address => uint256) public agentReputation;

    /// @notice Agents registered to receive θ signals
    mapping(address => bool) public registeredAgents;

    // --- Events ---

    event EpochMetricsReported(
        uint256 indexed epoch,
        uint256 qsr,
        bool isGreyZone,
        uint256 timestamp
    );

    event PMCPublished(
        uint256 indexed epoch,
        uint256 thetaRisk,
        uint256 thetaGas,
        uint256 thetaFinality
    );

    event AgentReputationUpdated(
        address indexed agent,
        uint256 oldScore,
        uint256 newScore,
        bool respectedSolvency
    );

    event AgentRegistered(address indexed agent);

    // --- Structs ---

    struct EpochMetrics {
        uint256 epoch;
        uint256 qsr;                    // Quantum Solvency Ratio (scaled 1e18)
        uint256 totalRewardsGwei;
        uint256 slashingPenaltyGwei;
        int256  netRebaseGwei;          // can be negative
        uint256 participationRate;      // scaled 1e4 (10000 = 100%)
        uint256 lidoTvlEth;
        uint256 mevProxyGwei;
        bool    isGreyZone;
        uint256 timestamp;
    }

    struct PMCSignal {
        uint256 epoch;
        uint256 thetaRisk;      // Risk coefficient (0-10000, scaled)
        uint256 thetaGas;       // Gas friction coefficient
        uint256 thetaLatency;   // Latency penalty coefficient
        uint256 thetaFinality;  // Finality risk coefficient
        uint256 thetaIncentives;// Incentive adjustment coefficient
        uint256 timestamp;
    }

    // --- Constructor ---

    constructor(address _operator) {
        operator = _operator;
    }

    // --- Modifiers ---

    modifier onlyOperator() {
        require(msg.sender == operator, "QUESTCore: not operator");
        _;
    }

    // --- Core Functions ---

    /**
     * @notice Report epoch metrics from the oracle node
     * @dev Called by the AVS operator after computing QSR off-chain
     */
    function reportEpochMetrics(
        uint256 epoch,
        uint256 qsr,
        uint256 totalRewardsGwei,
        uint256 slashingPenaltyGwei,
        int256  netRebaseGwei,
        uint256 participationRate,
        uint256 lidoTvlEth,
        uint256 mevProxyGwei,
        bool    isGreyZone
    ) external onlyOperator {
        latestMetrics = EpochMetrics({
            epoch: epoch,
            qsr: qsr,
            totalRewardsGwei: totalRewardsGwei,
            slashingPenaltyGwei: slashingPenaltyGwei,
            netRebaseGwei: netRebaseGwei,
            participationRate: participationRate,
            lidoTvlEth: lidoTvlEth,
            mevProxyGwei: mevProxyGwei,
            isGreyZone: isGreyZone,
            timestamp: block.timestamp
        });

        emit EpochMetricsReported(epoch, qsr, isGreyZone, block.timestamp);
    }

    /**
     * @notice Publish the Computational Monetary Policy signal (θ)
     * @dev Called after reportEpochMetrics. θ is derived from QSR off-chain.
     */
    function publishPMC(
        uint256 epoch,
        uint256 thetaRisk,
        uint256 thetaGas,
        uint256 thetaLatency,
        uint256 thetaFinality,
        uint256 thetaIncentives
    ) external onlyOperator {
        latestPMC = PMCSignal({
            epoch: epoch,
            thetaRisk: thetaRisk,
            thetaGas: thetaGas,
            thetaLatency: thetaLatency,
            thetaFinality: thetaFinality,
            thetaIncentives: thetaIncentives,
            timestamp: block.timestamp
        });

        emit PMCPublished(epoch, thetaRisk, thetaGas, thetaFinality);

        // Notify registered agents
        // Note: In production this would use a pull pattern to avoid gas issues
    }

    /**
     * @notice Update agent reputation based on behavior during epoch
     * @param agent Address of the autonomous agent
     * @param respectedSolvency True if agent reacted defensively to θ signal
     */
    function updateAgentReputation(
        address agent,
        bool respectedSolvency
    ) external onlyOperator {
        uint256 oldScore = agentReputation[agent];
        uint256 newScore;

        if (respectedSolvency) {
            // Reward: +100 reputation points (capped at 10000)
            newScore = oldScore + 100 > 10000 ? 10000 : oldScore + 100;
        } else {
            // Penalty: -200 reputation points (floored at 0)
            newScore = oldScore > 200 ? oldScore - 200 : 0;
        }

        agentReputation[agent] = newScore;
        emit AgentReputationUpdated(agent, oldScore, newScore, respectedSolvency);
    }

    /**
     * @notice Register as a QUEST-aware agent (ERC-8004)
     */
    function registerAgent() external {
        registeredAgents[msg.sender] = true;
        emit AgentRegistered(msg.sender);
    }

    // --- IERC8033 View Functions ---

    function getLatestQSR() external view override returns (uint256) {
        return latestMetrics.qsr;
    }

    function getLatestPMC() external view override returns (
        uint256 thetaRisk,
        uint256 thetaGas,
        uint256 thetaFinality
    ) {
        return (latestPMC.thetaRisk, latestPMC.thetaGas, latestPMC.thetaFinality);
    }

    function isGreyZone() external view override returns (bool) {
        return latestMetrics.isGreyZone;
    }

    function getEpochDensity() external view override returns (uint256) {
        // D_k = f(MEV, liquidez, slashings, participación, congestión)
        // Simplified version: weighted combination of available metrics
        uint256 mevWeight = latestMetrics.mevProxyGwei / 1e6;
        uint256 slashingWeight = latestMetrics.slashingPenaltyGwei / 1e6;
        uint256 participationFactor = latestMetrics.participationRate;

        return (mevWeight + slashingWeight) * participationFactor / 10000;
    }
}
