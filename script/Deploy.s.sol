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
