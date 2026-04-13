package oracle

import "math/big"

type ThetaSignal struct {
    ThetaRisk       *big.Int // 0-10000
    ThetaGas        *big.Int // 0-10000
    ThetaLatency    *big.Int // 0-10000 (constant 5000 in v1)
    ThetaFinality   *big.Int // 0-10000
    ThetaIncentives *big.Int // 0-10000
}

func DeriveTheta(greyZoneScore float64) ThetaSignal {
    thetaRisk := uint64(greyZoneScore * 10000)
    if thetaRisk > 10000 {
        thetaRisk = 10000
    }

    return ThetaSignal{
        ThetaRisk:       big.NewInt(int64(thetaRisk)),
        ThetaGas:        big.NewInt(5000),
        ThetaLatency:    big.NewInt(5000),
        ThetaFinality:   big.NewInt(int64(thetaRisk)),
        ThetaIncentives: big.NewInt(int64(10000 - thetaRisk)),
    }
}
