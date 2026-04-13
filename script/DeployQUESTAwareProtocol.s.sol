// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Script.sol";
import "../contracts/QUESTAwareProtocol.sol";

/**
 * @notice Deploys QUESTAwareProtocol pointing to an already-deployed QUESTCore.
 *
 * Usage:
 *   forge script script/DeployQUESTAwareProtocol.s.sol \
 *     --rpc-url $SEPOLIA_RPC_URL \
 *     --private-key $OPERATOR_PRIVATE_KEY \
 *     --broadcast \
 *     --verify \
 *     --etherscan-api-key $ETHERSCAN_API_KEY
 *
 * Required env vars:
 *   QUEST_CORE_ADDRESS  — deployed QUESTCore (Sepolia: 0xE81C6B16ecbEC8E4Aadc963e82B27c10c4ab10e7)
 *   RISK_TOLERANCE      — optional, defaults to 3e17 (30%)
 */
contract DeployQUESTAwareProtocol is Script {
    function run() external {
        address questCore    = vm.envAddress("QUEST_CORE_ADDRESS");
        uint256 riskTolerance = vm.envOr("RISK_TOLERANCE", uint256(3e17));

        vm.startBroadcast();
        QUESTAwareProtocol protocol = new QUESTAwareProtocol(questCore, riskTolerance);
        vm.stopBroadcast();

        console2.log("QUESTAwareProtocol deployed at:", address(protocol));
        console2.log("QUESTCore:                     ", questCore);
        console2.log("Risk tolerance (1e18 scale):   ", riskTolerance);
    }
}
