// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title IERC8033
 * @notice Macroprudential Stability Oracle Standard
 * @dev Standard interface for QUEST oracle. Allows any contract to read
 *      the systemic risk state of the Ethereum validator economy.
 *
 * Any protocol can integrate QUEST by reading:
 * - getLatestQSR(): Is the system solvent right now?
 * - isGreyZone(): Are there hidden slashings masked by rewards?
 * - getLatestPMC(): What is the recommended friction coefficient?
 */
interface IERC8033 {

    /**
     * @notice Returns the Quantum Solvency Ratio for the latest epoch
     * @return qsr Solvency ratio scaled 1e18. 1e18 = fully solvent. < 1e18 = at risk.
     */
    function getLatestQSR() external view returns (uint256 qsr);

    /**
     * @notice Returns the Computational Monetary Policy signal vector (θ)
     * @return thetaRisk    Systemic risk coefficient (0-10000)
     * @return thetaGas     Recommended gas friction multiplier
     * @return thetaFinality Finality risk coefficient
     */
    function getLatestPMC() external view returns (
        uint256 thetaRisk,
        uint256 thetaGas,
        uint256 thetaFinality
    );

    /**
     * @notice Returns true if current epoch is in a Grey Zone
     * @dev Grey Zone: net rebase is positive but incomplete slashings exist.
     *      This is the exact condition that bypasses Lido's Bunker Mode.
     */
    function isGreyZone() external view returns (bool);

    /**
     * @notice Returns the Epoch Temporal Density (D_k)
     * @dev D_k = f(MEV, liquidity, slashings, participation, congestion)
     */
    function getEpochDensity() external view returns (uint256);
}
