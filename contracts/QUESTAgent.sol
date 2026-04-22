// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "./interfaces/IERC8004QuestAware.sol";
import { UD60x18, ud, exp, ln } from "@prb/math/UD60x18.sol";

/**
 * @title QUESTAgent
 * @notice Autonomous DeFi agent whose exposure to LST-collateralized positions
 *         is governed by a mean-variance utility function parameterized by the
 *         QUEST Grey Zone Score (GZS).
 *
 * Utility function (Markowitz mean-variance):
 *
 *   U = E(R) - (lambda / 2) * sigma²(GZS)
 *
 * Systemic variance grows exponentially with GZS, capturing non-linear
 * tail-risk behavior near the Grey Zone threshold:
 *
 *   sigma²(GZS) = sigmaBase² * exp(k * GZS)
 *
 * Implemented via PRBMath UD60x18 fixed-point arithmetic.
 *
 * Exposure ratio (fraction of capital deployed in LST positions):
 *
 *   exposureRatio = clamp(U / E(R), 0, 1e18)
 *
 * When GZS is HEALTHY, exposure approaches 1e18 (100%).
 * As GZS rises, variance grows, utility compresses, exposure falls.
 * No external rule required — the utility function is the policy.
 *
 * Mean-variance efficient frontier (CAPM-style geometric interpretation):
 *
 *   E(Ra) = Rf + betaGZS * (E(Rm) - Rf)
 *
 * betaGZS is a design parameter, updated each epoch as
 * exposureRatio * maxBeta — not a statistical covariance estimate.
 */
contract QUESTAgent is IERC8004QuestAware {

    // --- Parameters (owner-configurable) ---

    address public immutable owner;
    address public immutable questCore;

    /// @notice Risk aversion coefficient λ ∈ [0, 1e18]. Higher = more conservative.
    uint256 public lambda;

    /// @notice Base standard deviation σ_base ∈ [0, 1e18].
    uint256 public sigmaBase;

    /// @notice Convexity multiplier k (scaled 1e18). Controls how fast variance
    ///         grows with GZS under sigma²(GZS) = sigmaBase² * exp(k * GZS).
    ///         Bounded to 1e19 (i.e. k ≤ 10) so that k * GZS stays well below
    ///         PRBMath's exp input cap (~133e18).
    uint256 public k;

    /// @notice Upper bound for k, enforced by constructor and setter.
    uint256 public constant K_MAX = 1e19;

    /// @notice Expected return per epoch E(R) ∈ [0, 1e18].
    uint256 public expectedReturn;

    /// @notice Maximum beta (full exposure coefficient). Scaled 1e18.
    uint256 public maxBeta;

    // --- State ---

    /// @notice Current exposure ratio ∈ [0, 1e18]. 1e18 = 100% deployed, 0 = fully withdrawn.
    uint256 public exposureRatio;

    /// @notice Current CAPM beta, derived from exposureRatio.
    uint256 public betaGZS;

    /// @notice Last computed utility (signed: negative = agent should exit entirely).
    int256 public lastUtility;

    /// @notice Last GZS received.
    uint256 public lastGreyZoneScore;

    /// @notice Last epoch processed.
    uint256 public lastEpoch;

    /// @notice Total signals received.
    uint256 public signalCount;

    // --- Events ---

    event ExposureAdjusted(
        uint256 indexed epoch,
        uint256 greyZoneScore,
        uint256 exposureRatio,
        uint256 betaGZS,
        int256  utility
    );

    // --- Constructor ---

    constructor(
        address _questCore,
        uint256 _lambda,
        uint256 _sigmaBase,
        uint256 _k,
        uint256 _expectedReturn,
        uint256 _maxBeta
    ) {
        require(_questCore != address(0), "QUESTAgent: zero questCore");
        require(_lambda     <= 1e18,      "QUESTAgent: lambda > 1");
        require(_sigmaBase  <= 1e18,      "QUESTAgent: sigmaBase > 1");
        require(_maxBeta    <= 1e18,      "QUESTAgent: maxBeta > 1");
        require(_k          <= K_MAX,     "QUESTAgent: k > K_MAX");

        owner          = msg.sender;
        questCore      = _questCore;
        lambda         = _lambda;
        sigmaBase      = _sigmaBase;
        k              = _k;
        expectedReturn = _expectedReturn;
        maxBeta        = _maxBeta;
        exposureRatio  = 1e18;
        betaGZS        = _maxBeta;
    }

    // --- IERC8004QuestAware ---

    function onQUESTSignal(
        uint256 epoch,
        uint256 greyZoneScore,
        uint256, /* thetaRisk */
        uint256, /* thetaFinality */
        bool
    ) external override {
        lastGreyZoneScore = greyZoneScore;
        lastEpoch         = epoch;
        signalCount++;

        int256 u     = computeUtility(greyZoneScore);
        uint256 expo = computeExposureRatio(greyZoneScore, u);
        uint256 beta = expo * maxBeta / 1e18;

        lastUtility   = u;
        exposureRatio = expo;
        betaGZS       = beta;

        emit ExposureAdjusted(epoch, greyZoneScore, expo, beta, u);
        emit StrategyAdjusted(epoch, greyZoneScore, bytes32(expo));
    }

    function getRiskTolerance() external view override returns (uint256) {
        // Risk tolerance expressed as the GZS at which exposure drops to 50%.
        //
        // exposure = U / E(R) = 1 - (lambda/2) * sigmaBase² * exp(k * GZS) / E(R)
        //
        // Setting exposure = 0.5 and solving:
        //   exp(k * GZS) = E(R) / (lambda * sigmaBase²)
        //   GZS         = ln(E(R) / (lambda * sigmaBase²)) / k
        if (lambda == 0 || sigmaBase == 0 || k == 0) return 1e18;

        // denom = lambda * sigmaBase² (scaled 1e18)
        uint256 denom = lambda * sigmaBase / 1e18 * sigmaBase / 1e18;
        if (denom == 0 || expectedReturn <= denom) return 0;

        // ratio (scaled 1e18) > 1e18 guaranteed by the check above
        uint256 ratio = expectedReturn * 1e18 / denom;
        UD60x18 lnRatio = ln(ud(ratio));
        return lnRatio.unwrap() * 1e18 / k;
    }

    function getQUESTReputation() external view override returns (uint256) {
        (bool ok, bytes memory data) = questCore.staticcall(
            abi.encodeWithSignature("agentReputation(address)", address(this))
        );
        if (!ok || data.length == 0) return 0;
        return abi.decode(data, (uint256));
    }

    // --- Math ---

    /**
     * @notice Computes agent utility given current GZS.
     *
     *   sigma²(GZS) = sigmaBase² * exp(k * GZS)
     *   U          = E(R) - (lambda / 2) * sigma²(GZS)
     *
     * Returns signed integer (negative = agent should fully exit).
     *
     * All intermediate fixed-point values are UD60x18 (1e18 scaled).
     * k * gzs is bounded by K_MAX (1e19) * 1e18 / 1e18 = 1e19, well below
     * PRBMath's exp input cap (~133e18), so no revert path in normal use.
     */
    function computeUtility(uint256 gzs) public view returns (int256) {
        // exponent = k * gzs / 1e18, scaled 1e18
        uint256 exponent = k * gzs / 1e18;
        // exp(exponent), scaled 1e18
        uint256 expTerm  = exp(ud(exponent)).unwrap();

        // sigma² = sigmaBase² * exp(k * gzs), scaled 1e18
        // multiply in stages to avoid overflow: sigmaBase ≤ 1e18
        uint256 sigmaSquared = sigmaBase * sigmaBase / 1e18 * expTerm / 1e18;

        // riskTerm = (lambda / 2) * sigma², scaled 1e18
        uint256 riskTerm = lambda * sigmaSquared / 2 / 1e18;

        if (expectedReturn >= riskTerm) {
            // forge-lint: disable-next-line(unsafe-typecast)
            // safe: expectedReturn - riskTerm ≤ expectedReturn ≤ type(uint256).max / 2
            return int256(expectedReturn - riskTerm);
        } else {
            // forge-lint: disable-next-line(unsafe-typecast)
            // safe: riskTerm - expectedReturn ≤ riskTerm ≤ type(uint256).max / 2
            return -int256(riskTerm - expectedReturn);
        }
    }

    /**
     * @notice Exposure ratio ∈ [0, 1e18] as a fraction of E(R).
     *
     *   exposureRatio = clamp(U / E(R), 0, 1e18)
     *
     * When U ≤ 0 or E(R) = 0: exposure = 0 (full exit).
     * When U ≥ E(R): exposure = 1e18 (full deployment).
     */
    function computeExposureRatio(uint256 /* gzs */, int256 u) public view returns (uint256) {
        if (u <= 0 || expectedReturn == 0) return 0;
        // forge-lint: disable-next-line(unsafe-typecast)
        // safe: u > 0 is checked above
        uint256 ratio = uint256(u) * 1e18 / expectedReturn;
        return ratio > 1e18 ? 1e18 : ratio;
    }

    /// @dev Convenience overload — computes utility internally.
    function computeExposureRatio(uint256 gzs) external view returns (uint256) {
        return computeExposureRatio(gzs, computeUtility(gzs));
    }

    // --- Owner ---

    function setLambda(uint256 _lambda) external {
        require(msg.sender == owner, "QUESTAgent: not owner");
        require(_lambda <= 1e18,     "QUESTAgent: lambda > 1");
        lambda = _lambda;
    }

    function setSigmaBase(uint256 _sigmaBase) external {
        require(msg.sender == owner,   "QUESTAgent: not owner");
        require(_sigmaBase <= 1e18,    "QUESTAgent: sigmaBase > 1");
        sigmaBase = _sigmaBase;
    }

    function setK(uint256 _k) external {
        require(msg.sender == owner, "QUESTAgent: not owner");
        require(_k <= K_MAX,         "QUESTAgent: k > K_MAX");
        k = _k;
    }

    function setExpectedReturn(uint256 _expectedReturn) external {
        require(msg.sender == owner, "QUESTAgent: not owner");
        expectedReturn = _expectedReturn;
    }

    function register() external {
        require(msg.sender == owner, "QUESTAgent: not owner");
        (bool ok,) = questCore.call(abi.encodeWithSignature("registerAgent()"));
        require(ok, "QUESTAgent: registration failed");
    }

    // --- View ---

    function status() external view returns (
        uint256 exposure,
        uint256 beta,
        int256  utility,
        uint256 gzs,
        uint256 epoch
    ) {
        return (exposureRatio, betaGZS, lastUtility, lastGreyZoneScore, lastEpoch);
    }
}
