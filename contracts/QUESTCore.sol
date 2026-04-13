// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "./interfaces/IERC8033.sol";

contract QUESTCore is IERC8033 {
    enum RiskLevel {
        UNSPECIFIED, // 0 — dato no disponible
        HEALTHY,     // 1 — greyZoneScore < 0.5e18
        GREY_ZONE,   // 2 — 0.5e18 <= greyZoneScore < 1e18
        CRITICAL     // 3 — greyZoneScore >= 1e18
    }

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

    address public immutable operator;
    EpochMetrics public latestMetrics;
    PMCSignal    public latestPMC;
    mapping(address => uint256) public agentReputation;  // 0-10000
    mapping(address => bool)    public registeredAgents;

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

    constructor(address _operator) {
        require(_operator != address(0), "QUESTCore: zero operator");
        operator = _operator;
    }

    modifier onlyOperator() {
        require(msg.sender == operator, "QUESTCore: not operator");
        _;
    }

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
    ) external onlyOperator {
        uint64 reportedAt = uint64(block.timestamp);

        latestMetrics = EpochMetrics({
            epoch: epoch,
            greyZoneScore: greyZoneScore,
            grossSlashingLossGwei: grossSlashingLossGwei,
            clRewardsGwei: clRewardsGwei,
            burnedEthGwei: burnedEthGwei,
            participationRate: participationRate,
            riskLevel: riskLevel,
            hasRewardsData: hasRewardsData,
            dataHash: dataHash,
            reportedAt: reportedAt
        });

        emit EpochMetricsReported(epoch, greyZoneScore, riskLevel, hasRewardsData, reportedAt);
    }

    function publishGreyZoneScore(
        uint64  epoch,
        uint256 thetaRisk,
        uint256 thetaGas,
        uint256 thetaLatency,
        uint256 thetaFinality,
        uint256 thetaIncentives
    ) external onlyOperator {
        uint64 publishedAt = uint64(block.timestamp);

        latestPMC = PMCSignal({
            epoch: epoch,
            thetaRisk: thetaRisk,
            thetaGas: thetaGas,
            thetaLatency: thetaLatency,
            thetaFinality: thetaFinality,
            thetaIncentives: thetaIncentives,
            publishedAt: publishedAt
        });

        emit GreyZoneScorePublished(epoch, thetaRisk, thetaFinality, publishedAt);
    }

    function updateAgentReputation(
        address agent,
        uint256 newScore
    ) external onlyOperator {
        if (newScore > 10000) {
            revert("QUESTCore: score > 10000");
        }
        uint256 oldScore = agentReputation[agent];
        agentReputation[agent] = newScore;
        emit AgentReputationUpdated(agent, oldScore, newScore);
    }

    function registerAgent() external {
        registeredAgents[msg.sender] = true;
        emit AgentRegistered(msg.sender);
    }

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
}
