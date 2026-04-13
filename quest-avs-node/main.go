package main

import (
    "context"
    "log"
    "os/signal"
    "syscall"

    "github.com/quest-protocol/quest-avs-node/config"
    "github.com/quest-protocol/quest-avs-node/oracle"
)

func main() {
    cfg := config.Load()

    runner, err := oracle.NewRunner(cfg)
    if err != nil {
        log.Fatalf("failed to initialize runner: %v", err)
    }

    ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGTERM, syscall.SIGINT)
    defer stop()

    log.Printf("QUEST AVS Node started")
    log.Printf("  Contract: %s", cfg.QuestCoreAddress)
    log.Printf("  API:      %s", cfg.QuestAPIURL)
    log.Printf("  Interval: %ds", cfg.PollIntervalSeconds)

    runner.Run(ctx)
    log.Println("QUEST AVS Node stopped.")
}
