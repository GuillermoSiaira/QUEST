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
