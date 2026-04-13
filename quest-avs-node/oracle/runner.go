package oracle

import (
    "context"
    "log"
    "time"

    "github.com/quest-protocol/quest-avs-node/config"
)

type Runner struct {
    cfg         *config.Config
    chainWriter *ChainWriter
    lastEpoch   int64
}

func NewRunner(cfg *config.Config) (*Runner, error) {
    chainWriter, err := NewChainWriter(cfg.SepoliaRPCURL, cfg.OperatorPrivateKey, cfg.QuestCoreAddress)
    if err != nil {
        return nil, err
    }

    return &Runner{
        cfg:         cfg,
        chainWriter: chainWriter,
        lastEpoch:   0,
    }, nil
}

func (r *Runner) Run(ctx context.Context) {
    ticker := time.NewTicker(time.Duration(r.cfg.PollIntervalSeconds) * time.Second)
    defer ticker.Stop()

    // First tick immediately — don't wait a full epoch on fresh deploy
    r.process()

    for {
        select {
        case <-ctx.Done():
            return
        case <-ticker.C:
            r.process()
        }
    }
}

func (r *Runner) process() {
    status, err := FetchLatestEpoch(r.cfg.QuestAPIURL)
    if err != nil {
        log.Printf("fetch latest epoch failed: %v", err)
        return
    }
    if status == nil || status.Epoch <= r.lastEpoch {
        log.Printf("no new epoch")
        return
    }

    tx1, err := r.chainWriter.ReportEpochMetrics(status)
    if err != nil {
        log.Printf("reportEpochMetrics failed: %v", err)
        return
    }

    theta := DeriveTheta(status.Risk.GreyZoneScore)
    tx2, err := r.chainWriter.PublishGreyZoneScore(uint64(status.Epoch), theta)
    if err != nil {
        log.Printf("publishGreyZoneScore failed: %v", err)
        return
    }

    r.lastEpoch = status.Epoch
    log.Printf(
        "Epoch %d submitted | score=%f | risk=%s | txs=%s,%s",
        status.Epoch,
        status.Risk.GreyZoneScore,
        status.Risk.RiskLevel,
        tx1.Hash().Hex(),
        tx2.Hash().Hex(),
    )
}
