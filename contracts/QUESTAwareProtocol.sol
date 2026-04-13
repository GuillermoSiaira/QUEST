// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "./interfaces/IERC8004QuestAware.sol";

/**
 * @title QUESTAwareProtocol
 * @notice Reference implementation of a DeFi protocol integrating QUEST
 *         macroprudential signals. Any protocol (lending, LST, treasury)
 *         can implement IERC8004QuestAware to receive risk signals and
 *         build on-chain reputation with the QUEST oracle.
 *
 * @dev This is a demonstration contract. In production, onQUESTSignal
 *      would trigger real DeFi operations (pause lending, reduce leverage,
 *      halt withdrawals). Here it emits events and tracks state.
 *
 *      QUEST is not an agent — it is infrastructure. This contract is
 *      an example of an external protocol consuming QUEST signals.
 */
contract QUESTAwareProtocol is IERC8004QuestAware {

    // --- State ---

    address public immutable owner;
    address public immutable questCore;

    /// @notice Max greyZoneScore this protocol tolerates before going defensive (1e18 scale)
    /// Default: 0.3e18 (30% — conservative)
    uint256 private _riskTolerance;

    /// @notice Current operational mode
    bool public isDefensive;

    /// @notice Last epoch signal received
    uint256 public lastSignalEpoch;

    /// @notice Last greyZoneScore received
    uint256 public lastGreyZoneScore;

    /// @notice Count of times protocol went defensive
    uint256 public defensiveCount;

    /// @notice Count of QUEST signals received total
    uint256 public signalCount;

    // --- Events ---

    /// @notice Emitted every time a QUEST signal is received
    event QUESTSignalReceived(
        uint256 indexed epoch,
        uint256 greyZoneScore,
        uint256 thetaRisk,
        bool    isGreyZone,
        bool    wentDefensive
    );

    /// @notice Emitted when protocol switches to defensive mode
    event DefensiveModeActivated(
        uint256 indexed epoch,
        uint256 greyZoneScore,
        string  reason
    );

    /// @notice Emitted when protocol returns to normal mode
    event NormalModeRestored(
        uint256 indexed epoch,
        uint256 greyZoneScore
    );

    // --- Constructor ---

    constructor(address _questCore, uint256 riskTolerance_) {
        require(_questCore != address(0), "QUESTAwareProtocol: zero questCore");
        require(riskTolerance_ <= 1e18,   "QUESTAwareProtocol: tolerance > 1e18");
        owner         = msg.sender;
        questCore     = _questCore;
        _riskTolerance = riskTolerance_ == 0 ? 3e17 : riskTolerance_;
    }

    // --- IERC8004QuestAware ---

    /**
     * @notice Called when QUEST publishes a new epoch signal.
     * @dev Permissionless — any caller can forward the signal.
     *      The protocol decides internally how to react based on its
     *      own riskTolerance threshold.
     */
    function onQUESTSignal(
        uint256 epoch,
        uint256 greyZoneScore,
        uint256 thetaRisk,
        uint256, /* thetaFinality — reserved for future use */
        bool    isGreyZone_
    ) external override {
        lastSignalEpoch   = epoch;
        lastGreyZoneScore = greyZoneScore;
        signalCount++;

        bool shouldBeDefensive = greyZoneScore >= _riskTolerance || isGreyZone_;
        bool wentDefensive     = false;

        if (shouldBeDefensive && !isDefensive) {
            isDefensive    = true;
            defensiveCount++;
            wentDefensive  = true;
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
        (bool ok, bytes memory data) = questCore.staticcall(
            abi.encodeWithSignature("agentReputation(address)", address(this))
        );
        if (!ok || data.length == 0) return 0;
        return abi.decode(data, (uint256));
    }

    // --- Owner functions ---

    /// @notice Register this protocol with QUESTCore. Only owner.
    function register() external {
        require(msg.sender == owner, "QUESTAwareProtocol: not owner");
        (bool ok,) = questCore.call(abi.encodeWithSignature("registerAgent()"));
        require(ok, "QUESTAwareProtocol: registration failed");
    }

    /// @notice Update risk tolerance. Only owner.
    function setRiskTolerance(uint256 newTolerance) external {
        require(msg.sender == owner,    "QUESTAwareProtocol: not owner");
        require(newTolerance <= 1e18,   "QUESTAwareProtocol: tolerance > 1e18");
        _riskTolerance = newTolerance;
    }

    // --- View ---

    /// @notice Returns a summary of the protocol's current QUEST-aware state.
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

        return (isDefensive, rep, _riskTolerance, signalCount, defensiveCount, lastSignalEpoch);
    }
}
