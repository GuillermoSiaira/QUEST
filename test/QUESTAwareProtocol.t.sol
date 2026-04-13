// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Test.sol";
import "../contracts/QUESTCore.sol";
import "../contracts/QUESTAwareProtocol.sol";

contract QUESTAwareProtocolTest is Test {
    event DefensiveModeActivated(
        uint256 indexed epoch,
        uint256 greyZoneScore,
        string reason
    );

    QUESTCore internal core;
    QUESTAwareProtocol internal protocol;

    function setUp() public {
        core = new QUESTCore(address(this));
        protocol = new QUESTAwareProtocol(address(core), 3e17);
    }

    function test_register_callsQuestCore() public {
        protocol.register();
        assertTrue(core.registeredAgents(address(protocol)));
    }

    function test_onQUESTSignal_healthyNoDefensive() public {
        protocol.onQUESTSignal(1, 1e17, 1000, 500, false);
        assertFalse(protocol.isDefensive());
        assertEq(protocol.signalCount(), 1);
    }

    function test_onQUESTSignal_exceedsTolerance_goesDefensive() public {
        protocol.onQUESTSignal(1, 5e17, 1000, 500, false);
        assertTrue(protocol.isDefensive());
        assertEq(protocol.defensiveCount(), 1);
    }

    function test_onQUESTSignal_greyZoneFlag_goesDefensive() public {
        protocol.onQUESTSignal(1, 1e17, 1000, 500, true);
        assertTrue(protocol.isDefensive());
    }

    function test_onQUESTSignal_recovers_toNormal() public {
        protocol.onQUESTSignal(1, 5e17, 1000, 500, false);
        assertTrue(protocol.isDefensive());
        protocol.onQUESTSignal(2, 1e17, 1000, 500, false);
        assertFalse(protocol.isDefensive());
    }

    function test_onQUESTSignal_emitsDefensiveModeActivated() public {
        vm.expectEmit(true, false, false, true);
        emit DefensiveModeActivated(
            1,
            5e17,
            "greyZoneScore exceeded risk tolerance"
        );
        protocol.onQUESTSignal(1, 5e17, 1000, 500, false);
    }

    function test_setRiskTolerance_onlyOwner() public {
        vm.prank(address(0xBEEF));
        vm.expectRevert("QUESTAwareProtocol: not owner");
        protocol.setRiskTolerance(5e17);

        protocol.setRiskTolerance(5e17);
        assertEq(protocol.getRiskTolerance(), 5e17);
    }

    function test_status_returnsCorrectFields() public {
        protocol.onQUESTSignal(1, 1e17, 1000, 500, false);
        (
            bool defensive,
            uint256 reputation,
            uint256 tolerance,
            uint256 signals,
            uint256 defensiveTriggers,
            uint256 lastEpoch
        ) = protocol.status();

        assertFalse(defensive);
        assertEq(reputation, 0);
        assertEq(tolerance, 3e17);
        assertEq(signals, 1);
        assertEq(defensiveTriggers, 0);
        assertEq(lastEpoch, 1);
    }
}
