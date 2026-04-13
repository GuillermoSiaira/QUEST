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
