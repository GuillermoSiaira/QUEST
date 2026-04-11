// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title IERC8004QuestAware
 * @notice Interface for autonomous agents that react to QUEST macroprudential signals
 * @dev Agents implementing this interface declare themselves "QUEST-aware".
 *      They agree to adjust their strategy based on θ signals in exchange for
 *      ERC-8004 reputation score improvements.
 *
 * This is the key integration point for the Agent Economy layer.
 * AI funds, liquidation bots, and protocol treasuries implement this interface.
 */
interface IERC8004QuestAware {

    /// @notice Emitted when an agent adjusts strategy due to QUEST signal
    event StrategyAdjusted(
        uint256 indexed epoch,
        uint256 thetaRisk,
        bytes32 actionTaken
    );

    /**
     * @notice Called by QUEST (or any party) when a new PMC signal is published
     * @dev Agents should implement defensive logic here:
     *      - If thetaRisk > threshold: reduce leverage, pause new positions, etc.
     *      - QUEST will monitor on-chain behavior and update reputation accordingly
     * @param epoch         Current epoch number
     * @param thetaRisk     Risk coefficient (0-10000). 8000+ = high risk.
     * @param thetaGas      Gas friction recommendation
     * @param thetaFinality Finality risk level
     * @param isGreyZone    True if hidden slashings detected
     */
    function onQUESTSignal(
        uint256 epoch,
        uint256 thetaRisk,
        uint256 thetaGas,
        uint256 thetaFinality,
        bool isGreyZone
    ) external;

    /**
     * @notice Returns the agent's current risk tolerance threshold
     * @dev QUEST uses this to evaluate if the agent is behaving consistently
     *      with its declared risk profile
     */
    function getRiskTolerance() external view returns (uint256);

    /**
     * @notice Returns the agent's current QUEST reputation score
     * @dev Fetched from QUESTCore. Higher = more "systemic-risk-aware" agent.
     */
    function getQUESTReputation() external view returns (uint256);
}
