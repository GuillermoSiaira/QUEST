// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Test.sol";
import "../contracts/QUESTAgent.sol";

/**
 * @dev Reference calibration (matches dashboard AgentPanel.tsx):
 *
 *   lambda         = 0.6   (6e17)
 *   sigmaBase      = 0.05  (5e16)
 *   k              = ln(10) ~ 2.302585 (2302585092994045684)
 *   expectedReturn = 0.0075 (7.5e15)
 *   maxBeta        = 1.0   (1e18)
 *
 * Target curve:
 *   exposure(GZS = 0.0)  ~ 90%
 *   exposure(GZS = 0.5)  ~ 68%
 *   exposure(GZS = 1.0)  ~ 0%
 *
 * Note: with exponential variance, the 50% point lands near GZS ~ 0.7,
 * not 0.5 — consistent with the paper's narrative that systemic risk
 * accelerates non-linearly near the CRITICAL threshold.
 */
contract QUESTAgentTest is Test {
    QUESTAgent internal agent;
    address    internal questCore = address(0xC0DE);

    uint256 constant LAMBDA      = 6e17;
    uint256 constant SIGMA_BASE  = 5e16;
    uint256 constant K           = 2302585092994045684; // ln(10) * 1e18
    uint256 constant E_R         = 75e14;               // 0.0075 * 1e18
    uint256 constant MAX_BETA    = 1e18;

    function setUp() public {
        agent = new QUESTAgent(questCore, LAMBDA, SIGMA_BASE, K, E_R, MAX_BETA);
    }

    function test_calibration_gzsZero_exposureNinetyPct() public view {
        uint256 expo = agent.computeExposureRatio(0);
        // target 90% ± 1%
        assertApproxEqAbs(expo, 9e17, 1e16, "GZS=0 should give ~90% exposure");
    }

    function test_calibration_gzsOne_exposureZero() public view {
        uint256 expo = agent.computeExposureRatio(1e18);
        // target 0% ± 0.5%
        assertApproxEqAbs(expo, 0, 5e15, "GZS=1 should give ~0% exposure");
    }

    function test_calibration_gzsHalf_exposureAboveLinear() public view {
        // With exponential form and (90%, 0%) calibration, exposure(0.5)
        // should be above the linear midpoint 45% — the convexity signature.
        uint256 expo = agent.computeExposureRatio(5e17);
        assertGt(expo, 45e16, "exponential form: exposure(0.5) > 45%");
        assertLt(expo, 80e16, "exponential form: exposure(0.5) < 80%");
    }

    function test_utility_monotonicallyDecreasing_inGzs() public view {
        int256 u0   = agent.computeUtility(0);
        int256 u25  = agent.computeUtility(25e16);
        int256 u50  = agent.computeUtility(50e16);
        int256 u75  = agent.computeUtility(75e16);
        int256 u100 = agent.computeUtility(1e18);

        assertGt(u0,  u25,  "U decreasing");
        assertGt(u25, u50,  "U decreasing");
        assertGt(u50, u75,  "U decreasing");
        assertGt(u75, u100, "U decreasing");
    }

    function test_exposureRatio_clampedToZero_whenUtilityNegative() public view {
        // At GZS well above 1.0, utility should be negative → exposure 0.
        uint256 expo = agent.computeExposureRatio(15e17);
        assertEq(expo, 0, "negative U clamps exposure to 0");
    }

    function test_riskTolerance_returnsHalfExposurePoint() public view {
        // Analytical: GZS where exposure = 50%.
        // exp(k * GZS) = E(R) / (lambda * sigmaBase²)
        //              = 7.5e15 / (6e17 * (5e16)²/1e18)
        //              = 7.5e15 / (6e17 * 2.5e15 / 1e18)
        //              = 7.5e15 / 1.5e15 = 5
        // GZS = ln(5) / k = 1.609438 / 2.302585 ~ 0.69897
        uint256 tol = agent.getRiskTolerance();
        assertApproxEqAbs(tol, 699e15, 5e15, "risk tolerance ~ 0.699");

        // Verify: exposure at that GZS should be ~50%.
        uint256 expoAtTol = agent.computeExposureRatio(tol);
        assertApproxEqAbs(expoAtTol, 5e17, 1e16, "exposure at tolerance ~ 50%");
    }

    function test_onQuestSignal_updatesStateAndBeta() public {
        // Simulate signal from questCore.
        vm.prank(questCore);
        agent.onQUESTSignal(42, 5e17, 0, 0, false);

        (uint256 exposure, uint256 beta, int256 utility, uint256 gzs, uint256 epoch) =
            agent.status();

        assertEq(epoch, 42);
        assertEq(gzs, 5e17);
        assertGt(exposure, 0);
        assertEq(beta, exposure * MAX_BETA / 1e18);
        assertGt(utility, 0);
    }
}
