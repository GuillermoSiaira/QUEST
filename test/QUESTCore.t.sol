// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Test.sol";
import "../contracts/QUESTCore.sol";

contract QUESTCoreTest is Test {
    event GreyZoneScorePublished(
        uint64 indexed epoch,
        uint256 thetaRisk,
        uint256 thetaFinality,
        uint64 publishedAt
    );

    QUESTCore internal core;
    address internal alice = address(0xA11CE);

    function setUp() public {
        core = new QUESTCore(address(this));
    }

    function test_reportEpochMetrics_storesCorrectly() public {
        core.reportEpochMetrics(
            12,
            6e17,
            100,
            200,
            300,
            9000,
            QUESTCore.RiskLevel.GREY_ZONE,
            true,
            bytes32(keccak256("hash"))
        );

        (
            uint64 epoch,
            uint256 greyZoneScore,
            ,
            ,
            ,
            ,
            QUESTCore.RiskLevel riskLevel,
            ,
            ,

        ) = core.latestMetrics();

        assertEq(epoch, 12);
        assertEq(greyZoneScore, 6e17);
        assertEq(uint8(riskLevel), uint8(QUESTCore.RiskLevel.GREY_ZONE));
    }

    function test_reportEpochMetrics_revertsIfNotOperator() public {
        vm.prank(address(0xBEEF));
        vm.expectRevert("QUESTCore: not operator");
        core.reportEpochMetrics(
            1,
            1e18,
            0,
            0,
            0,
            10000,
            QUESTCore.RiskLevel.HEALTHY,
            true,
            bytes32(0)
        );
    }

    function test_publishGreyZoneScore_emitsEvent() public {
        vm.warp(12345);
        vm.expectEmit(true, false, false, true);
        emit GreyZoneScorePublished(7, 8000, 4000, 12345);
        core.publishGreyZoneScore(7, 8000, 2000, 3000, 4000, 5000);
    }

    function test_isGreyZone_trueWhenGreyZone() public {
        core.reportEpochMetrics(
            2,
            7e17,
            0,
            0,
            0,
            9000,
            QUESTCore.RiskLevel.GREY_ZONE,
            true,
            bytes32(0)
        );
        assertTrue(core.isGreyZone());
    }

    function test_isGreyZone_trueWhenCritical() public {
        core.reportEpochMetrics(
            3,
            12e17,
            0,
            0,
            0,
            9000,
            QUESTCore.RiskLevel.CRITICAL,
            true,
            bytes32(0)
        );
        assertTrue(core.isGreyZone());
    }

    function test_isGreyZone_falseWhenHealthy() public {
        core.reportEpochMetrics(
            4,
            4e17,
            0,
            0,
            0,
            9000,
            QUESTCore.RiskLevel.HEALTHY,
            true,
            bytes32(0)
        );
        assertFalse(core.isGreyZone());
    }

    function test_updateAgentReputation_setsScore() public {
        core.updateAgentReputation(alice, 5000);
        assertEq(core.agentReputation(alice), 5000);
    }

    function test_updateAgentReputation_revertsAbove10000() public {
        vm.expectRevert("QUESTCore: score > 10000");
        core.updateAgentReputation(alice, 10001);
    }

    function test_registerAgent_idempotent() public {
        core.registerAgent();
        core.registerAgent();
        assertTrue(core.registeredAgents(address(this)));
    }

    function test_dataHash_storedCorrectly() public {
        bytes32 dataHash = keccak256("test");
        core.reportEpochMetrics(
            5,
            5e17,
            0,
            0,
            0,
            10000,
            QUESTCore.RiskLevel.HEALTHY,
            true,
            dataHash
        );

        (
            ,
            ,
            ,
            ,
            ,
            ,
            ,
            ,
            bytes32 storedDataHash,

        ) = core.latestMetrics();

        assertEq(storedDataHash, dataHash);
    }
}
