package oracle

import (
    "encoding/json"
    "fmt"
    "io"
    "net/http"
    "time"
)

type RiskAssessment struct {
    Epoch                int64   `json:"epoch"`
    GrossSlashingLossEth float64 `json:"gross_slashing_loss_eth"`
    ClRewardsEth         float64 `json:"cl_rewards_eth"`
    BurnedEth            float64 `json:"burned_eth"`
    GreyZoneScore        float64 `json:"grey_zone_score"`
    RiskLevel            string  `json:"risk_level"` // "HEALTHY" | "GREY_ZONE" | "CRITICAL"
    HasRewardsData       bool    `json:"has_rewards_data"`
}

type EpochStatus struct {
    Epoch                 int64          `json:"epoch"`
    TotalValidators       int64          `json:"total_validators"`
    TotalActiveBalanceEth float64        `json:"total_active_balance_eth"`
    SlashedValidators     int64          `json:"slashed_validators"`
    SlashingPenaltyEth    float64        `json:"slashing_penalty_eth"`
    EpochRewardsEth       *float64       `json:"epoch_rewards_eth"`
    ParticipationRate     float64        `json:"participation_rate"`
    AvgGasPriceGwei       float64        `json:"avg_gas_price_gwei"`
    BurnedEth             float64        `json:"burned_eth"`
    LidoTvlEth            float64        `json:"lido_tvl_eth"`
    NetRebaseEth          *float64       `json:"net_rebase_eth"`
    IsGreyZone            bool           `json:"is_grey_zone"`
    Risk                  RiskAssessment `json:"risk"`
}

func FetchLatestEpoch(apiURL string) (*EpochStatus, error) {
    client := &http.Client{Timeout: 15 * time.Second}
    resp, err := client.Get(apiURL + "/api/status")
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()

    if resp.StatusCode == http.StatusNoContent {
        return nil, nil
    }
    if resp.StatusCode != http.StatusOK {
        return nil, fmt.Errorf("unexpected status: %d", resp.StatusCode)
    }

    body, err := io.ReadAll(resp.Body)
    if err != nil {
        return nil, err
    }
    if len(body) == 0 {
        return nil, nil
    }

    var status EpochStatus
    if err := json.Unmarshal(body, &status); err != nil {
        return nil, err
    }
    return &status, nil
}
